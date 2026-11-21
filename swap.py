"""Replay the EUR/CHF swap with the same inputs as the Excel scenario sheet."""

import argparse
from datetime import date
from pathlib import Path

import numpy as np
from openpyxl import load_workbook


def read_inputs():
    workbook = load_workbook(
        Path(__file__).with_name("AlpineSwap.xlsx"), read_only=True, data_only=True
    )
    try:
        rows = workbook["Inputs"].iter_rows(min_row=2, max_row=18, max_col=2, values_only=True)
        return dict(rows)
    finally:
        workbook.close()


def fixing_years(inputs):
    """The first coupon fixes one year after the contract starts."""
    first = inputs["start_date"].year + 1
    return range(first, first + 15)


def present_values(inputs, shocks):
    """Return one discounted cash flow per scenario and annual payment date."""
    shocks = np.asarray(shocks, dtype=float)
    if shocks.ndim != 2 or shocks.shape[1] != 15 or not np.isfinite(shocks).all():
        raise ValueError("Supply 15 finite annual shocks for each scenario.")
    start = inputs["start_date"].date()
    dates = [date(start.year + year, start.month, start.day) for year in range(16)]
    days = np.array([(end - begin).days for begin, end in zip(dates, dates[1:])])
    dt = days / 365
    # EUR/CHF is quoted in francs per euro. The forward drift uses CHF minus EUR rates.
    vol = inputs["volatility"]
    increments = (inputs["chf_rate"] - inputs["eur_rate"] - 0.5 * vol**2) * dt
    log_fx = np.cumsum(increments + vol * np.sqrt(dt) * shocks, axis=1)
    fx = inputs["spot_fx"] * np.exp(log_fx)

    pay_rate = inputs["base_coupon"] + np.where(
        fx < inputs["barrier"], inputs["strike"] / fx - 1, 0
    )
    pay_rate[:, :2] = inputs["first_coupon"]
    pay_rate[:, 2:4] = inputs["second_coupon"]

    repayments = inputs["first_repayment"] * (1 + inputs["repayment_growth"]) ** np.arange(15)
    # Interest uses the principal at the start of each payment period.
    principal = inputs["principal"] - np.r_[0, np.cumsum(repayments[:-1])]
    net = principal * (inputs["receive_rate"] - pay_rate) * days / 360
    discount = (1 + inputs["eur_rate"] + inputs["discount_margin"]) ** (-np.cumsum(dt))
    return net * discount


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=int, help="Number of FX scenarios")
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument(
        "--stress-year", type=int, help="Change one annual shock in the zero-shock path"
    )
    parser.add_argument(
        "--stress-sigma", type=float, default=-2.0, help="Shock in standard deviations"
    )
    args = parser.parse_args()
    inputs = read_inputs()
    paths = inputs["scenario_count"] if args.paths is None else args.paths
    if paths < 1:
        parser.error("--paths must be positive")
    rng = np.random.default_rng(args.seed)
    values = present_values(inputs, rng.standard_normal((paths, 15))).sum(axis=1)
    baseline = present_values(inputs, np.zeros((1, 15)))[0]
    print(f"Scenarios: {paths:,}   Seed: {args.seed}")
    print(f"Zero-shock present value: EUR {baseline.sum():,.2f}")
    if args.stress_year is not None:
        years = fixing_years(inputs)
        if args.stress_year not in years or not np.isfinite(args.stress_sigma):
            parser.error(
                f"Choose a fixing year between {years[0]} and {years[-1]} and a finite shock."
            )
        stress = np.zeros((1, len(years)))
        stress[0, years.index(args.stress_year)] = args.stress_sigma
        stressed = present_values(inputs, stress).sum()
        print(
            f"{args.stress_year} shock of {args.stress_sigma:g} standard deviations: EUR {stressed:,.2f}"
        )
    print(f"Mean present value: EUR {values.mean():,.2f}")
    print(f"Fifth percentile: EUR {np.quantile(values, 0.05):,.2f}")
    print(f"Share of scenarios with a loss: {np.mean(values < 0):.2%}")


if __name__ == "__main__":
    main()
