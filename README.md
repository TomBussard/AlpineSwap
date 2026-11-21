# AlpineSwap

A municipal borrower receives a fixed 5.10 percent coupon and pays a rate linked to EUR/CHF on an amortising loan. I examined how a stronger Swiss franc changes the borrower's payments over fifteen years, and why a few early savings can coexist with a large loss over the life of the swap.

## Scenario tools

I built two ways to examine the contract. In Excel, **Inputs** holds the loan, FX, coupon and discount assumptions. **Scenario** follows one set of annual shocks, so a single cell change can be traced through the fixing, barrier, debt outstanding and net payment. The optional VBA routine switches to random shocks, recalculates one path at a time and writes its full value and two selected annual payments into **Runs**.

In Python I can repeat a fixed path, stress any one fixing year, choose the number of Monte Carlo paths and fix the random seed. The simulation returns a matrix with one discounted cash flow per path and year. That lets me study a particular payment, the whole swap, or how two years move together. [Workbook](AlpineSwap.xlsx) · [Python scenario engine](swap.py) · [Excel batch routine](vba/ScenarioAnalysis.bas)

## Follow one payment

Open the [Excel workbook](AlpineSwap.xlsx). The **Inputs** sheet contains the market assumptions. **Scenario** follows each annual fixing through the coupon, outstanding principal and discounted net cash flow. Change the fixed shock on one row to see how the rest of the path changes. The public edition follows the original workbook's introductory coupons of 2.00 percent for two years and 3.50 percent for two more. From year five, a fixing below 1.47 triggers the extra coupon.

The 2014 row in the original workbook checked the 2014 barrier but used the 2013 fixing inside the payoff. I corrected both parts to use the same year's fixing. Each Python step also uses the elapsed time between payment dates. This keeps the Brownian increment independent of how many scenarios are simulated.

## What the model produced

With 10,000 simulated paths and seed 2025, the mean discounted net cash flow was **EUR -35.67 million**. The fifth percentile was **EUR -65.14 million**, and **98.23 percent** of simulated paths ended below zero. These are outcomes under the case's specified rates and volatility. The zero-shock path gives EUR -34.62 million in Excel and Python.

![Distribution of discounted swap cash flows across 10,000 simulated currency paths](figures/swap-distribution.png)

## Check a fixing against the workbook

| Discounted value to the borrower | EUR |
| --- | ---: |
| Fifteen annual shocks set to zero | -34,621,290.55 |
| Change only the 2014 shock to -2 standard deviations | -45,759,578.17 |
| Difference | -11,138,287.62 |

### From a currency fixing to a euro payment

I quote $S_i$ in Swiss francs per euro. Let $d_i$ be the number of days in period $i$, $\Delta t_i=d_i/365$ and $Z_i$ its standard normal shock. The model advances from the previous fixing using constant EUR and CHF rates and annual FX volatility of 3% ($\sigma=0.03$).

```math
\log(S_i/S_{i-1})=(r_{\mathrm{CHF}}-r_{\mathrm{EUR}}-\tfrac12\sigma^2)\Delta t_i+\sigma\sqrt{\Delta t_i}\,Z_i
```

For the first four payments the contract uses the introductory coupons above. From year five the borrower pays a base rate of 2.57%, with an additional amount when the fixing is strictly below 1.47.

```math
c_i=0.0257+\begin{cases}1.54/S_i-1 & S_i<1.47\\0 & S_i\ge 1.47\end{cases}
```

Let $P_i$ be the principal left after all earlier repayments and $t_i$ the elapsed years on an actual/365 basis. The borrower receives 5.10% on that principal. Interest accrues on actual/360 and each annual net receipt is discounted at 5.12% plus a 0.50% margin.

```math
PV_i=\frac{P_i(0.051-c_i)\,d_i/360}{(1+0.0512+0.0050)^{t_i}},\qquad PV=\sum_{i=1}^{15}PV_i
```

In 2014 the opening principal is **EUR 39.04 million**. On the zero-shock path the fixing is **1.2745**, the payable coupon is **23.40%** and that year's discounted net payment is **EUR −5.22 million**. A shock of −2 moves the fixing to **1.2003**, raises the coupon to **30.87%** and changes that payment to **EUR −7.35 million**. Across all fifteen payments the shock reduces the swap's value by **EUR 11.14 million** because the lower FX level also feeds subsequent fixings. [FX path, repayment schedule and discounting](swap.py) · [Scenario worksheet](AlpineSwap.xlsx)

To compare Excel and Python, set the **2014** shock in the Scenario sheet to -2 and leave every other shock at zero. This is a deterministic comparison at the contract level. The distribution above is a separate Monte Carlo run under the workbook's fixed rates and volatility.

```sh
python swap.py --paths 10000 --seed 2025 --stress-year 2014 --stress-sigma -2
```

## Amortisation and the distribution of losses

The loan opens at **EUR 52.483 million**. Its first scheduled principal repayment is EUR 2.43218228 million and subsequent repayments grow by 5% each year. If $A_j$ is repayment $j$ and $N$ the original principal, interest for period $i$ is calculated on

```math
A_j=A_1(1+g)^{j-1},\qquad P_i=N-\sum_{j=1}^{i-1}A_j.
```

Five earlier repayments bring the 2014 opening balance to **EUR 39.04366 million**. As the loan amortises, an identical coupon change produces a smaller euro payment on a smaller balance. A shock to FX persists on the path and can still alter whether future fixings cross the barrier.

For each path $k$ I add its fifteen discounted coupon differences to obtain $V_k$. The simulation reports the sample mean, an empirical fifth percentile and the fraction of paths with negative net value to the borrower. The standard error measures sampling variability in the estimated mean for these fixed inputs.

```math
\bar V=\frac{1}{M}\sum_{k=1}^{M}V_k,\qquad
\widehat{\mathrm{SE}}(\bar V)=\frac{s(V)}{\sqrt M},\qquad
\widehat p_{\rm loss}=\frac{1}{M}\sum_{k=1}^{M}\mathbf{1}_{\{V_k<0\}}.
```

| Repeated calculation, 10,000 paths and seed 2025 | Output |
| --- | ---: |
| Mean path value | EUR −35.672 million |
| Standard deviation across individual paths | EUR 17.409 million |
| Standard error of the mean | EUR 0.174 million |
| Fifth percentile of path values | EUR −65.135 million |
| Correlation between the discounted 2014 and 2020 payments | 0.699 |

The two annual payments average **EUR −5.355 million** and **EUR −2.850 million** respectively. They are positively correlated because they share the earlier currency shocks. That dependence is preserved when valuing the swap as a whole.

```python
import numpy as np
from swap import fixing_years, present_values, read_inputs

inputs = read_inputs()
shocks = np.random.default_rng(2025).standard_normal((10_000, 15))
cashflows = present_values(inputs, shocks)
years = list(fixing_years(inputs))
payments = cashflows[:, [years.index(2014), years.index(2020)]]
print(cashflows.sum(axis=1).std(ddof=1) / np.sqrt(len(cashflows)))
print(np.corrcoef(payments.T)[0, 1])
```

## Reproduce the study

```sh
python -m pip install -r requirements.txt
python swap.py --paths 10000 --seed 2025
```

The [Python model](swap.py) reads the same inputs as Excel. To run a batch inside desktop Excel, save a copy of the workbook as an Excel macro-enabled workbook, import [ScenarioAnalysis.bas](vba/ScenarioAnalysis.bas) and run `RunScenarios`. Each row of **Runs** records the full swap and its 2014 and 2020 payments on the same path. The fixed shocks in **Scenario** can be used without macros.

Tom Bussard
