"""
Forecasting Access and Usage, 2025-2027.

Combines two things built in earlier tasks:
- A trend regression fit on historical Findex points (simple OLS via numpy/scipy, with a
  proper prediction interval formula -- degrees-of-freedom aware, so a 2-point series like
  USG_DIGITAL_PAYMENT honestly produces a much wider/undefined interval than a 5-point series,
  rather than a falsely precise-looking one).
- The event-effect model from Task 3 (src/impact_model.py), applied forward in time to
  events whose ramp isn't yet fully realized as of the last actual data point -- i.e. an
  "event-augmented" forecast layered on top of the pure trend.

Scenarios (optimistic/base/pessimistic) vary the Task-3-calibrated dampening factor, since
that's this project's single largest, most explicit source of modeling uncertainty.

Implemented with numpy/scipy.stats rather than statsmodels, so the exact same prediction-
interval math (standard simple-linear-regression formula) is fully transparent and has no
extra dependency beyond what data_loader.py already needs.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats

from src.data_loader import get_observations
from src.impact_model import get_effects_for_indicator, ramp, dampening_for


@dataclass
class TrendModel:
    slope: float
    intercept: float
    n: int
    x_mean: float
    sxx: float          # sum((x - x_mean)^2)
    residual_std: float  # s = sqrt(SSE / (n-2)), NaN if n<=2
    df_resid: int

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.intercept + self.slope * np.asarray(x)


def fit_trend(df: pd.DataFrame, indicator_code: str, gender_filter: str | None = "all") -> tuple[TrendModel, pd.DataFrame]:
    """OLS regression of value on year (decimal years), implemented directly so the
    prediction-interval math is fully visible and doesn't require statsmodels."""
    obs = get_observations(df)
    obs = obs[obs["indicator_code"] == indicator_code]
    if gender_filter is not None and "gender" in obs.columns:
        obs = obs[obs["gender"] == gender_filter]
    obs = obs.sort_values("observation_date")

    x = (obs["observation_date"].dt.year + (obs["observation_date"].dt.dayofyear - 1) / 365.25).values
    y = obs["value_numeric"].values
    n = len(x)

    slope, intercept = np.polyfit(x, y, 1)
    x_mean = x.mean()
    sxx = np.sum((x - x_mean) ** 2)
    df_resid = n - 2

    if df_resid > 0:
        y_hat = intercept + slope * x
        sse = np.sum((y - y_hat) ** 2)
        residual_std = np.sqrt(sse / df_resid)
    else:
        residual_std = np.nan  # not enough points for a meaningful residual estimate

    model = TrendModel(slope=slope, intercept=intercept, n=n, x_mean=x_mean,
                        sxx=sxx, residual_std=residual_std, df_resid=df_resid)
    return model, obs


def trend_prediction(model: TrendModel, years: list[float], alpha: float = 0.05) -> pd.DataFrame:
    """Point forecast + prediction interval for a list of decimal years."""
    years = np.asarray(years)
    point = model.predict(years)

    if model.df_resid > 0 and model.sxx > 0:
        se_pred = model.residual_std * np.sqrt(1 + 1 / model.n + (years - model.x_mean) ** 2 / model.sxx)
        t_crit = stats.t.ppf(1 - alpha / 2, df=model.df_resid)
        margin = t_crit * se_pred
        ci_lower, ci_upper = point - margin, point + margin
    else:
        # Not enough residual degrees of freedom (e.g. a 2-point series) for a
        # statistically meaningful interval -- return NaN rather than a falsely
        # precise-looking number.
        ci_lower = np.full_like(point, np.nan)
        ci_upper = np.full_like(point, np.nan)

    return pd.DataFrame({"year": years, "trend_forecast": point, "ci_lower": ci_lower, "ci_upper": ci_upper})


def future_event_effect(df: pd.DataFrame, indicator_code: str, t_last_actual: pd.Timestamp,
                         t_forecast: pd.Timestamp, dampening: float = 1.0) -> float:
    """Incremental effect (pp) of all events linked to this indicator, between the last
    actual data point and a future forecast date -- same ramp/incremental logic as Task 3."""
    effects = get_effects_for_indicator(df, indicator_code)
    total = 0.0
    for e in effects:
        r0 = ramp(t_last_actual, e.event_date, e.lag_months)
        r1 = ramp(t_forecast, e.event_date, e.lag_months)
        total += e.magnitude_pp * (r1 - r0) * dampening_for(e, dampening)
    return total


def event_augmented_forecast(df: pd.DataFrame, indicator_code: str, model: TrendModel,
                              t_last_actual: pd.Timestamp, actual_last_value: float,
                              forecast_years: list[int], dampening: float = 1.0) -> pd.DataFrame:
    """Trend's implied incremental change from the last actual point, plus the incremental
    event effect over the same window, applied on top of the actually-observed last value."""
    year_decimal_last = t_last_actual.year + (t_last_actual.dayofyear - 1) / 365.25
    trend_at_last = model.predict(np.array([year_decimal_last]))[0]

    rows = []
    for year in forecast_years:
        t_forecast = pd.Timestamp(f"{year}-12-31")
        year_decimal = year + (365 - 1) / 365.25
        trend_at_forecast = model.predict(np.array([year_decimal]))[0]
        trend_incremental = trend_at_forecast - trend_at_last

        event_incremental = future_event_effect(df, indicator_code, t_last_actual, t_forecast, dampening=dampening)

        forecast_value = actual_last_value + trend_incremental + event_incremental
        rows.append({
            "year": year, "trend_component": trend_incremental,
            "event_component": event_incremental, "forecast": forecast_value,
        })
    return pd.DataFrame(rows)


def scenario_forecast(df: pd.DataFrame, indicator_code: str, model: TrendModel,
                       t_last_actual: pd.Timestamp, actual_last_value: float,
                       forecast_years: list[int],
                       dampening_scenarios: dict[str, float]) -> pd.DataFrame:
    """Run event_augmented_forecast under multiple dampening assumptions (scenarios)."""
    all_scenarios = []
    for name, d in dampening_scenarios.items():
        result = event_augmented_forecast(df, indicator_code, model, t_last_actual,
                                           actual_last_value, forecast_years, dampening=d)
        result["scenario"] = name
        all_scenarios.append(result)
    return pd.concat(all_scenarios, ignore_index=True)
