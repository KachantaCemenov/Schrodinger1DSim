HELP_TOPICS = [
    (
        "Solvers",
        [
            ("Numerical Solvers\n", "title"),
            ("A solver calculates the result of the wave function - which, in this program, is a 1D matrix of probability density in space - at the next step in time"
                 "in the selected problem, potential, spacial grid, and time step."
                 "This application provides two methods at the time of this writing.\n\n", None),
            ("Crank–Nicolson (CN)\n", "heading"),
            ("Crank-Nicolson uses finite differences to represent spatial derivatives and solves an equation of tridiagonal matrices at each time step.\n\n", None),
            ( "• Supports the Infinite Square Well in Simulation, with the wave fixed to zero at the walls.\n", "bullet"),
            ( "• Problems with large grid points and time steps produce significantly large errors.\n\n", "bullet"),

            ("Split-Step Fourier (SSF)\n", "heading"),
            ("Split-Step Fourier separates evolution into potential and kinetic parts. It applies the potential in position space and uses Fourier transforms to apply the kinetic "
                "part in momentum space.\n\n", None),
            ("• In current implementation in this program, SSF requires periodic boundaries:"
             "a wave leaving one edge of the domain will re-enter at the opposite edge.\n", "bullet"),
            ("• The current implementation does not support the Infinite Square Well due to requirement of periodic boundaries.\n\n", "bullet"),

            ("Choosing a solver: ", "bold"),
            ("Neither method is always the best choice. Use Benchmark to compare accuracy and recorded runtime, then use "
                "Recommendation to find a tested configuration that meets your requirements.\n\n", None),
            ("Small norm or energy drift alone does not guarantee an accurate wave function. L2 is the prominent value for that (more on L2 on another page)", "italic"),
        ],
    ),
    (
        "Topic 2",
        [
            ("Placeholder Title\n", "title"),
            ("TODO: Write the second topic here.\n", None),
        ],
    ),
    (
        "Topic 3",
        [
            ("Placeholder Title\n", "title"),
            ("TODO: Write the third topic here.\n", None),
        ],
    ),
    (
        "Topic 4",
        [
            ("Placeholder Title\n", "title"),
            ("TODO: Write the fourth topic here.\n", None),
        ],
    ),
]