# Theory: every equation the solver uses

All equations come from Smith, Van Ness & Abbott, *Introduction to Chemical Engineering Thermodynamics* (SVN), and so do the data, except for two species the book does not cover (see [DATA_SOURCES.md](DATA_SOURCES.md)). Section, table and equation numbers below are those of the 8th edition; the 7th edition has the same content with slightly different numbering (for example the chemical-equilibrium chapter is Chapter 13 there and Chapter 14 in the 8th).

Each block names the Python function that implements it, so the code can be checked line by line against this page.

## 0. Conventions

| Quantity | Value | Source |
|---|---|---|
| Gas constant R | 8.314 J/(mol·K) = 83.14 cm³·bar/(mol·K) | SVN Table A.2 |
| Reference temperature T₀ | 298.15 K | SVN Table C.4 |
| Standard-state pressure P° | 1 bar | SVN Sec. 4.3 |
| Air | 21 mol-% O₂, 79 mol-% N₂ | SVN Ch. 4 examples |

- **Standard state** (SVN Sec. 4.3): the pure species at 1 bar, at the temperature of interest. Gases are in the ideal-gas state; liquids and solids are the real pure substance. The standard state fixes the pressure, not the temperature: ΔH°(T), ΔS°(T) and ΔG°(T) are standard property changes at any T. 298.15 K is the reference temperature T₀ at which Table C.4 lists the formation data, nothing more.
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

**Below 298.15 K.** Tables C.1 and C.2 are valid from 298 K. From 200 K to 298.15 K the solver uses a second set of constants for the same form, with D = 0,

    Cp/R = A + B·T + C·T²        (200 K ≤ T < 298.15 K)

computed from NIST tables (see [DATA_SOURCES.md](DATA_SOURCES.md); `species.low_temperature_sets`, `heatcap.quadratic_with_integral`, `heatcap.quadratic_through`). `Species.coeffs_at(T)` returns the set that applies at T. Because every integral in this file runs from T₀ = 298.15 K to T, and the two sets meet exactly at T₀, an integral never crosses from one set to the other, and all formulas below hold unchanged with the constants of the side T lies on. A sensible heat between two temperatures on opposite sides of T₀ is taken in two parts. H, S and G are continuous at T₀; Cp itself has a small step there, the difference between the two sources.

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

Reading K: ΔG° < 0 means K > 1, products favoured when every species is in its standard state. It says nothing about rate, and the actual conversion also depends on pressure and feed composition (Section 6). ΔG° > 0 does not mean that nothing reacts, only that K < 1, and it takes nothing away from ΔH°: the heat of reaction is a difference of state functions and exists for any balanced reaction. It is the heat exchanged per mole that does react, and the heat of the reverse reaction with the opposite sign.

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

## 8. Extra feature 2: the heat lab (SVN Sec. 4.5 to 4.7, and the bomb-calorimeter lab)

### 8.1 Energy balance on a reactor (`heatbalance.solve`)

For a steady-flow reactor with no shaft work and negligible kinetic and potential energy changes, the first law is

    Q = ΔH = H_out(T_out) − H_in(T_in)

per mole of the key reactant fed. Enthalpy is a state function, so ΔH is evaluated along the path SVN uses for industrial reactions: take the feed to 298.15 K, react there, take the products to the outlet temperature.

    ΔH_R    = Σ n_in,i  ∫ from T_in to T₀  of Cp,i dT        (feed to 298.15 K)
    ΔH°₂₉₈  = Σ_j ξ_j ΔH°₂₉₈,j                               (ξ_j = extent of reaction j)
    ΔH_P    = Σ n_out,i ∫ from T₀ to T_out of Cp,i dT        (products to the outlet)
    Q       = ΔH_R + ΔH°₂₉₈ + ΔH_P

The same Q is Σ n_out,i Hᵢ(T_out) − Σ n_in,i Hᵢ(T_in) with Hᵢ(T) = ΔH°f,ᵢ + ∫Cp dT, because Σ n_out ΔH°f − Σ n_in ΔH°f = Σ ξ_j ΔH°₂₉₈,j. The solver evaluates both routes and shows that they agree.

Two questions are answered with it:

- **Heat duty**: T_out is given, Q is the result.
- **Outlet temperature**: Q is given (0 for an adiabatic reactor) and T_out is the unknown, found from H_out(T_out) = H_in(T_in) + Q by Newton's method kept inside a bracket (`heatbalance.outlet_temperature`). With complete combustion and Q = 0 this is the theoretical flame temperature. In the book's own notation the solution satisfies T = T₀ − ΔH°₂₉₈/⟨Cp⟩_H when the feed enters at T₀.

The heat capacities of a mixture add, so each stream has one set of constants (Σ nᵢAᵢ, Σ nᵢBᵢ, ...) and one enthalpy polynomial (`heatbalance.Stream`).

**Feed and outlet** (`heatbalance.build_case`), per mole of key reactant:

    n_in(reactant r) = |ν_r| / |ν_key| × (1 + excess of r)
    n_in(N₂)        += (79/21) × n_in(O₂)          when the oxygen comes as air
    n_out,i          = n_in,i + Σ_j ν_i,j ξ_j       with ξ_main = conversion / |ν_key|

A setting that would leave a negative amount of any species is rejected.

**Where the search is allowed to go.** A polynomial heat capacity can turn negative far outside the range it was fitted to (methane's does above about 4400 K, graphite's below about 210 K). The outlet-temperature search stays in the interval around 298.15 K where the summed heat capacity of the outlet stream is positive, so the enthalpy rises with temperature and the balance has one solution. If the balance has no solution there, the solver says so and suggests what to change. Inside that interval, a species used outside its own fitted range still raises the usual extrapolation warning.

**Assumptions**, the same as in SVN's examples: every species stays in the phase written, the gases are ideal, and the reactions go to the stated extents. In particular no dissociation is considered, so above about 2000 K real flames are cooler than the calculated value.

### 8.2 Work that the hot products could deliver (`heatbalance.work_potential`)

Cooling the outlet stream to the temperature of the surroundings T_σ at constant pressure and composition, the ideal work (SVN Chapter 5) is

    W_ideal = ΔH − T_σ ΔS          ΔH = Σ nᵢ ∫ Cp,i dT,   ΔS = Σ nᵢ ∫ Cp,i dT/T    from T_out to T_σ

It is negative when the stream can deliver work. If the heat is simply discarded, all of it is lost work. For comparison the solver also gives 1 − T_σ/T_out, the Carnot efficiency of an engine supplied at the constant temperature T_out; the stream does less because its temperature falls while it gives up heat.

### 8.3 Fuel facts (`heatbalance.fuel_facts`, `heatbalance.heating_values`)

For the complete combustion of a fuel made of C, H, O, N and S,

    CxHyOzNwSv + (x + y/4 + v − z/2) O₂ → x CO₂ + (y/2) H₂O + (w/2) N₂ + v SO₂

- **Lower heating value** = −ΔH°₂₉₈ with the water as vapour; **higher heating value** = −ΔH°₂₉₈ with the water as liquid. Their difference is the heat of vaporisation of the water formed.
- **Stoichiometric air** = moles of O₂ / 0.21.

### 8.4 Bomb calorimeter (`heatbalance.calorimeter_run`, `heatbalance.identify_fuel`)

The bomb is a closed, rigid vessel: W = 0, so the heat released is the change of internal energy, with the water formed as liquid. From H = U + PV and ideal gases,

    ΔU_c = ΔH_c − Δn_gas·R·T            Δn_gas counts gaseous species only
    calorific value = −ΔU_c / M          per gram of fuel

These are the relations of the course lab handout. The calorimeter constant comes from a calibration run with a standard of known calorific value, and the temperature rise of a sample follows from it:

    C_cal = (m_std × CV_std + ignition corrections) / ΔT_std
    ΔT    = (m × CV + ignition corrections) / C_cal

Run in reverse, a measured ΔT gives the calorific value of an unknown sample, which is compared with the liquid and solid fuels of the database. The handout's shortcut LHV = HHV − m_w·h_fg is shown next to the lower heating value from formation data; the two differ only by the small Δn_gas·R·T term.

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
| Atoms in the reactor | atoms in the feed = atoms in the outlet, every element |
| Two routes to the heat duty | ΔH_R + ΔH°₂₉₈ + ΔH_P = Σ n_out Hᵢ(T_out) − Σ n_in Hᵢ(T_in) |
| Energy balance closes | H_out(T_out) − H_in(T_in) = Q |

Derivatives are central finite differences, so they share no code with the formulas they test.
