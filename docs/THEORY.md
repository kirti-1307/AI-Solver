# Theory: every equation the solver uses

All equations come from Smith, Van Ness & Abbott, *Introduction to Chemical Engineering Thermodynamics* (SVN), and so do the data, except for two species the book does not cover (see [DATA_SOURCES.md](DATA_SOURCES.md)). Section, table and equation numbers below are those of the 8th edition; the 7th edition has the same content with slightly different numbering (for example the chemical-equilibrium chapter is Chapter 13 there and Chapter 14 in the 8th).

Each block names the Python function that implements it, so the code can be checked line by line against this page.

## 0. Conventions

| Quantity | Value | Source |
|---|---|---|
| Gas constant R | 8.314 J/(mol·K) = 83.14 cm³·bar/(mol·K) | SVN Table A.2 |
| Reference temperature T₀ | 298.15 K | SVN Table C.4 |
| Standard-state pressure P° | 1 bar | SVN Sec. 4.3 |
| Faraday constant F | 96,485 C/mol | SVN Sec. 14.10 |

- **Standard state** (SVN Sec. 4.3): the pure species at 1 bar. Gases are in the ideal-gas state; liquids and solids are the real pure substance.
- **Stoichiometric numbers** νᵢ are positive for products and negative for reactants. Every property change of reaction is ΔM = Σ νᵢ Mᵢ, per mole of reaction as written.
- **Units** in the code: T in K, P in bar, energy in J/mol, entropy in J/(mol·K), volume in cm³/mol.

## 1. Heat capacity and sensible heat (SVN Sec. 4.1)

Heat capacity polynomial, with constants from Tables C.1 (gases), C.2 (solids) and C.3 (liquids):

    Cp/R = A + B·T + C·T² + D·T⁻²

Its two integrals between T₀ and T (`heatcap.icph`, `heatcap.icps`):

    ∫ (Cp/R) dT   = A(T − T₀) + (B/2)(T² − T₀²) + (C/3)(T³ − T₀³) + D(T − T₀)/(T·T₀)
    ∫ (Cp/R) dT/T = A ln(T/T₀) + [B + (C + D/(T₀²T²))·(T + T₀)/2]·(T − T₀)

**One extension for data from outside SVN.** The NIST Chemistry WebBook publishes heat capacities as a Shomate equation, Cp = a + b·t + c·t² + d·t³ + e/t² with t = T/1000, which has a cubic term. So that such an equation can be used exactly as published, the code carries an optional fifth coefficient:

    Cp/R = A + B·T + C·T² + D·T⁻² + E·T³

which adds (E/4)(T⁴ − T₀⁴) to the first integral and (E/3)(T³ − T₀³) to the second. E is zero for every SVN species, so for them nothing changes. It is non-zero only for hydrogen peroxide and acetic acid vapour (see [DATA_SOURCES.md](DATA_SOURCES.md)).

Mean heat capacities (`heatcap.mcph`, `heatcap.mcps`), in the form used on the course slides:

    ⟨Cp⟩_H / R = A + (B/2)(T + T₀) + (C/3)(T² + T₀² + T·T₀) + D/(T·T₀)
    ⟨Cp⟩_S / R = [∫ (Cp/R) dT/T] / ln(T/T₀)

Sensible heat of one species with no phase change (`Species.sensible_dH`):

    Q = ΔH = R ∫ (Cp/R) dT = ⟨Cp⟩_H (T₂ − T₁)

## 2. Standard heat of reaction (SVN Sec. 4.3 to 4.6)

At 298.15 K, from the heats of formation in Table C.4 (`Reaction.dH0`):

    ΔH°₂₉₈ = Σ νᵢ ΔH°f,ᵢ

This is Hess's law: each compound's formation reaction is added νᵢ times and the elements cancel.

At any other temperature (`Reaction.dH`), with ΔCp°/R = ΔA + ΔB·T + ΔC·T² + ΔD·T⁻² and Δ(·) = Σ νᵢ (·)ᵢ:

    ΔH°(T) = ΔH°₂₉₈ + R ∫ (ΔCp°/R) dT = ΔH°₂₉₈ + ⟨ΔCp°⟩_H (T − T₀)

The path behind it: cool the reactants from T to T₀, react at T₀, heat the products from T₀ to T. The solver reports the three terms separately.

## 3. Entropy and Gibbs energy of reaction, equilibrium constant (SVN Sec. 14.3 and 14.4)

SVN tabulates ΔH°f and ΔG°f but not absolute entropies. The entropy change at 298.15 K follows from the definition G = H − TS (`Reaction.dS0`):

    ΔS°₂₉₈ = (ΔH°₂₉₈ − ΔG°₂₉₈) / T₀

At temperature T (`Reaction.dS`, `Reaction.dG`, `Reaction.lnK`):

    ΔS°(T) = ΔS°₂₉₈ + R ∫ (ΔCp°/R) dT/T
    ΔG°(T) = ΔH°(T) − T·ΔS°(T)
           = ΔH°₂₉₈ − (T/T₀)(ΔH°₂₉₈ − ΔG°₂₉₈) + R ∫ (ΔCp°/R) dT − R·T ∫ (ΔCp°/R) dT/T
    ln K   = −ΔG°(T) / (R·T)

The last line of ΔG°(T) is the closed form SVN gives; the solver evaluates it both ways and the audit checks that they agree.

Reading K: ΔG° < 0 means K > 1, products favoured when every species is in its standard state. It says nothing about rate, and the actual conversion also depends on pressure and feed composition (Section 6).

**Simplified treatments shown for comparison** (`Reaction.dH_constant_cp`, `Reaction.dG_no_cp`): ΔCp° frozen at its 298.15 K value, and ΔCp° ignored altogether. These are the shortcuts that the assignment's stress test 2 asks about; the solver never uses them for its own results.

## 4. Building a reaction from other reactions (SVN Sec. 4.4)

If a target reaction is the linear combination target = Σ mⱼ·(reaction j), then because H, S and G are state functions (`combine.combine_reactions`):

    ΔH = Σ mⱼ ΔHⱼ        ΔS = Σ mⱼ ΔSⱼ        ΔG = Σ mⱼ ΔGⱼ
    ln K = Σ mⱼ ln Kⱼ     so     K = Π Kⱼ^mⱼ

A negative multiplier reverses a reaction. The solver computes the target both by summing the steps and directly from the net stoichiometry, and reports the difference (zero to round-off).

## 5. Pressure effects and residual properties (SVN Ch. 3 and Ch. 6)

A residual property is the real-gas value minus the ideal-gas value at the same T and P: Mᴿ = M − Mⁱᵍ. The enthalpy of an ideal gas does not depend on pressure, so **at constant temperature the residual enthalpy is the whole effect of pressure on H**.

For a reaction, taking each reactant and product as the pure species at T and P (`realgas.reaction_at_pressure`):

    ΔH(T,P) = ΔH°(T) + Σ νᵢ Hᵢᴿ(T,P)
    ΔS(T,P) = ΔS°(T) − R·Δν_gas·ln(P/P°) + Σ νᵢ Sᵢᴿ(T,P)
    ΔG(T,P) = ΔH(T,P) − T·ΔS(T,P) = ΔG°(T) + R·T Σ_gas νᵢ ln(φᵢ·P/P°)

Sums run over the gaseous species. Solids and liquids are taken as incompressible, with negligible pressure dependence and unit activity.

### 5.1 Generalized virial-coefficient correlation (SVN Eq. 3.61, 3.62 and 6.70, 6.71)

    B⁰ = 0.083 − 0.422/Tr^1.6          dB⁰/dTr = 0.675/Tr^2.6
    B¹ = 0.139 − 0.172/Tr^4.2          dB¹/dTr = 0.722/Tr^5.2
    Z          = 1 + (B⁰ + ω·B¹)·Pr/Tr
    Hᴿ/(R·Tc)  = Pr·[B⁰ − Tr·dB⁰/dTr + ω·(B¹ − Tr·dB¹/dTr)]
    Sᴿ/R       = −Pr·(dB⁰/dTr + ω·dB¹/dTr)
    ln φ       = (Pr/Tr)·(B⁰ + ω·B¹)

Implemented in `realgas.residual` (model `virial`). Two details:

- **Rounded constants.** 0.675 and 0.722 are 0.422 × 1.6 = 0.6752 and 0.172 × 4.2 = 0.7224 rounded to three figures. With the rounded values Hᴿ and Sᴿ disagree with ln φ by up to 0.06 %, which the consistency audit detects. The solver uses the unrounded products.
- **Hydrogen** is a quantum gas. SVN (Eq. 3.54 to 3.56) gives temperature-dependent effective critical constants to be used with ω = 0: Tc/K = 43.6/(1 + 21.8/(2.016·T)), Pc/bar = 20.5/(1 + 44.2/(2.016·T)). Because Tc then depends on T, dB/dT is taken numerically for hydrogen.

The truncated virial equation is for low to moderate pressure. The solver warns when the reduced volume V/Vc falls below 2 (a common rule of thumb for the region where SVN's comparison figure shows the correlation departing from Lee/Kesler).

### 5.2 Generic cubic equation of state (SVN Sec. 3.6, Table 3.1; residuals worked in Example 13.5 and Table 13.7, which are Example 6.4 and Table 6.3 in earlier editions)

    P = R·T/(V − b) − a(T)/[(V + ε·b)(V + σ·b)]
    b = Ω·R·Tc/Pc        a(T) = Ψ·α(Tr)·R²·Tc²/Pc
    β = Ω·Pr/Tr          q = Ψ·α(Tr)/(Ω·Tr)

| Equation | α(Tr) | σ | ε | Ω | Ψ |
|---|---|---|---|---|---|
| van der Waals | 1 | 0 | 0 | 1/8 | 27/64 |
| Redlich/Kwong | Tr^(−1/2) | 1 | 0 | 0.08664 | 0.42748 |
| Soave/Redlich/Kwong | [1 + (0.480 + 1.574ω − 0.176ω²)(1 − Tr^½)]² | 1 | 0 | 0.08664 | 0.42748 |
| Peng/Robinson | [1 + (0.37464 + 1.54226ω − 0.26992ω²)(1 − Tr^½)]² | 1 + √2 | 1 − √2 | 0.07780 | 0.45724 |

Compressibility factor (the vapour-like root is the largest real root with Z > β):

    Z = 1 + β − q·β·(Z − β)/[(Z + ε·β)(Z + σ·β)]

The solver rearranges this into the cubic polynomial Z³ + c₂Z² + c₁Z + c₀ = 0 and solves it analytically (`realgas.cubic_Z_roots`), then polishes the roots with Newton's method. The test-suite substitutes every root back into the pressure-explicit equation above.

Residual properties (`realgas._cubic_properties`):

    I       = [1/(σ − ε)]·ln[(Z + σ·β)/(Z + ε·β)]        (I = β/Z for van der Waals)
    Hᴿ/(RT) = Z − 1 + [d ln α/d ln Tr − 1]·q·I
    Sᴿ/R    = ln(Z − β) + (d ln α/d ln Tr)·q·I
    ln φ    = Z − 1 − ln(Z − β) − q·I

with d ln α/d ln Tr = 0 (van der Waals), −1/2 (Redlich/Kwong), and −κ·Tr^½/[1 + κ(1 − Tr^½)] for SRK and PR, where κ is the polynomial in ω.

Two implementation details:

- **Very high reduced temperature.** For SRK and PR the term 1 + κ(1 − Tr^½) falls to zero far above Tc (for nitrogen with SRK at about 1030 K). Its square would rise again beyond that point, which is unphysical, so α is held at zero there. The code works with dα/d ln Tr = α·(d ln α/d ln Tr) = −κ·Tr^½·[1 + κ(1 − Tr^½)], which stays finite, so Z, φ, Hᴿ and Sᴿ are continuous.
- **Which root is it?** Below Tc the cubic can have three real roots. The largest is used for a gas. If the liquid root has the lower fugacity, the pure species would really be a liquid; the vapour root is then a *hypothetical vapour*, which is exactly the state the ideal-solution rule needs for a species that is dilute in a gas mixture, and the solver says so. If only one root is left and its molar volume is below the critical volume the same equation predicts (Z·Tr/Pr < Zc of the equation: 3/8, 1/3, 1/3, 0.3074), it is a liquid root. The solver then reports no gas-phase value at all, and refuses to use it in an equilibrium calculation.

### 5.3 Is it really a gas? (SVN Eq. 6.92 to 6.94)

A gas-phase residual property is meaningless if the species would condense. The solver estimates the vapour pressure with the Lee/Kesler correlation and warns when P exceeds it:

    ln Pr_sat = ln Pr⁰ + ω·ln Pr¹
    ln Pr⁰ = 5.92714 − 6.09648/Tr − 1.28862·ln Tr + 0.169347·Tr⁶
    ln Pr¹ = 15.2518 − 15.6875/Tr − 13.4721·ln Tr + 0.43577·Tr⁶

It is a corresponding-states estimate (within about 10 % for water), so it is used for warnings only, never inside a property calculation and never to decide which root of a cubic equation is which (Section 5.2 does that from the equation itself).

### 5.4 Assumption to keep in mind

Residual properties here are those of the **pure** species at T and P. Using them for a reacting mixture is the ideal-solution (Lewis/Randall) approximation: no heat of mixing, and φ̂ᵢ = φᵢ.

## 6. Equilibrium conversion of one reaction (SVN Sec. 14.6 and 14.7)

With the reaction coordinate ε, nᵢ = nᵢ₀ + νᵢ·ε, and unit activity for pure solids and liquids (`equilibrium.reaction_equilibrium`):

    Π_gas (yᵢ·φᵢ)^νᵢ = K·(P/P°)^(−ν_gas)

The left side increases monotonically with ε, so the equation is solved by bisection between the limits where a reactant or product runs out. A gas-solid reaction whose only gas is a product (limestone calcination) has no interior solution: it either does not start or goes to completion, and K = P_CO₂/P° gives the decomposition pressure.

## 7. Extra feature 1: competing reactions by Gibbs-energy minimisation (SVN Sec. 14.9, Example 14.14)

For a gas mixture of N species and w elements, the equilibrium state minimises the total Gibbs energy subject to conservation of every element (`equilibrium.gibbs_minimize`):

    G/RT = Σ nᵢ·[Gᵢ°(T)/RT + ln(yᵢ·φᵢ·P/P°)]
    subject to   Σ nᵢ·aᵢₖ = Aₖ      for each element k

Stationarity with Lagrange multipliers πₖ = λₖ/RT gives one equation per species:

    Gᵢ°/RT + ln(yᵢ·φᵢ·P/P°) = Σₖ πₖ·aᵢₖ

No list of reactions is needed: the species list alone decides what can form.

- **Gᵢ°(T)** is the species Gibbs energy on the formation scale, Gᵢ°(T) = [ΔH°f,ᵢ + ∫Cp dT] − T·[ΔS°f,ᵢ + ∫Cp dT/T] (`Species.G`). It differs from ΔG°f,ᵢ(T) by a term that depends only on the elements, which cannot change the minimum because the elements are conserved. For any balanced reaction Σ νᵢ Gᵢ°(T) is exactly ΔG°(T) of Section 3.
- **Numerical method**: Newton's method on the stationarity and balance equations in the variables ln nᵢ, the scheme of NASA's CEA program. Working in ln nᵢ keeps every mole number positive and handles trace species.
- **Carbon activity**: the multiplier of carbon is the chemical potential of elemental carbon in the gas. If π_C exceeds G°_graphite/RT, graphite would lower G further. The solver reports a_C = exp(π_C − G°_graphite/RT); a_C > 1 means coke formation is thermodynamically favoured.

Validation: with the ΔG°f values quoted in SVN's example (CH₄/H₂O/CO/CO₂/H₂ at 1000 K and 1 bar) the solver returns the book's mole fractions to four decimals, and for a single reaction it reproduces the reaction-coordinate result of Section 6.

## 8. Extra feature 2: electrochemical lens (SVN Sec. 14.10)

A reaction run reversibly in an electrochemical cell at constant T and P exchanges electrical work equal to its Gibbs energy change (`electrochem.electrochemistry`):

    W_elec = ΔG                         Q_rev = T·ΔS = ΔH − ΔG
    E_rev  = −ΔG/(n·F)                  E_tn  = −ΔH/(n·F)
    dE_rev/dT = ΔS/(n·F)

n is the number of electrons per mole of reaction: 4 per O₂, otherwise 2 per H₂ or Cl₂, or entered by hand. Hydrogen peroxide is the exception, because its oxygen is at oxidation state −1: when it takes part, n is 2 per H₂ or, without H₂, 2 per O₂.

- ΔG < 0: a **fuel cell**. Ideal efficiency ΔG/ΔH, compared with the Carnot limit 1 − Tc/T of a heat engine burning the same fuel.
- ΔG > 0: an **electrolyser**. Minimum electricity ΔG; the remainder T·ΔS of the energy demand ΔH can be supplied as heat. E_tn is the voltage at which the cell neither heats nor cools.
- At pressure P the same ΔG(T,P) of Section 5 is used, which is the Nernst equation for pure gases at P.

## 9. Consistency audit (`audit.py`)

Every result is re-derived by an independent numerical route. A wrong formula, sign or unit breaks at least one of these.

| Check | Identity |
|---|---|
| Elemental balance | atoms in = atoms out for every element |
| Two routes to ΔG°(T) | closed form of Section 3 = Σ νᵢ Gᵢ°(T) |
| Kirchhoff | d(ΔH°)/dT = ΔCp° |
| van 't Hoff | d ln K/dT = ΔH°/(R·T²) |
| Gibbs-Helmholtz | d(ΔG°)/dT = −ΔS° |
| Integrals | analytical ∫Cp dT and ∫Cp dT/T = Simpson quadrature |
| Residual Gibbs energy | Hᴿ − T·Sᴿ = R·T·ln φ |
| Residual Gibbs-Helmholtz | (∂ ln φ/∂T)_P = −Hᴿ/(R·T²) |
| Volume relation | (∂ ln φ/∂P)_T = (Z − 1)/P |

Derivatives are central finite differences, so they share no code with the formulas they test.
