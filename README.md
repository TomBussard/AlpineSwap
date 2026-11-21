# AlpineSwap

A municipal borrower receives a fixed 5.10 percent coupon and pays a rate linked to EUR/CHF on an amortising loan. I examined how a stronger Swiss franc changes the borrower's payments over fifteen years, and why a few early savings can coexist with a large loss over the life of the swap.

## Follow one payment

Open the [Excel workbook](AlpineSwap.xlsx). The **Inputs** sheet contains the market assumptions. **Scenario** follows each annual fixing through the coupon, outstanding principal and discounted net cash flow. Change the fixed shock on one row to see how the rest of the path changes. The public edition follows the original workbook's introductory coupons of 2.00 percent for two years and 3.50 percent for two more. From year five, a fixing below 1.47 triggers the extra coupon.

The 2014 row in the original workbook checked the 2014 barrier but used the 2013 fixing inside the payoff. I corrected both parts to use the same year's fixing. Each Python step also uses the elapsed time between payment dates. This keeps the Brownian increment independent of how many scenarios are simulated.

## What the model produced

With 10,000 simulated paths and seed 2025, the mean discounted net cash flow was **EUR -35.67 million**. The fifth percentile was **EUR -65.14 million**, and **98.23 percent** of simulated paths ended below zero. These are outcomes under the case's specified rates and volatility. The zero-shock path gives EUR -34.62 million in Excel and Python.

![Distribution of discounted swap cash flows across 10,000 simulated currency paths](figures/swap-distribution.png)

## Reproduce the study

```sh
python -m pip install -r requirements.txt
python swap.py --paths 10000 --seed 2025
```

The [Python model](swap.py) reads the same inputs as Excel. To run a batch inside desktop Excel, save a copy of the workbook as an Excel macro-enabled workbook, import [ScenarioAnalysis.bas](vba/ScenarioAnalysis.bas) and run `RunScenarios`. Each row of **Runs** records the full swap and its 2014 and 2020 payments on the same path. The fixed shocks in **Scenario** can be used without macros.

Portfolio by **Tom Bussard**, March 2025.

