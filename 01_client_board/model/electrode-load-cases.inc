* electrode-load-cases.inc  --  dummy-head load cases shared by T04..T07, selected by LD.
*  LD  RS     RE (each)  CE (each)  CC     what it is
*   1  1k     -          -          -      bench resistor, low end
*   2  10k    -          -          -      bench resistor, high end
*   3  1k     -          -          1n     1k + 1 nF lead capacitance (~5 m of shielded cable)
*   4  500    1k         1u         100p   gel electrodes on skin (ASSUMED values)
*   5  1k     5k         100n       100p   poorer skin contact (ASSUMED)
*   6  300    10k        10n        100p   dry / small electrodes (ASSUMED)
* Replace 4..6 with the measured dummy-head values when you have them.
.param LD=1
.param HRS={table(LD,1,1k,2,10k,3,1k,4,500,5,1k,6,300)}
.param HRE={table(LD,1,1m,2,1m,3,1m,4,1k,5,5k,6,10k)}
.param HCE={table(LD,1,1p,2,1p,3,1p,4,1u,5,100n,6,10n)}
.param HCC={table(LD,1,1p,2,1p,3,1n,4,100p,5,100p,6,100p)}
