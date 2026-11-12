from Recommendation import BuildRecommendationSummary, FindRecommendation


if __name__ == "__main__":
    folder = input("Saved benchmark run folder: ").strip().strip('"')

    manifest, summary = BuildRecommendationSummary(folder)

    print(f"\nCompleted combinations: {manifest['completed_combinations']} / {manifest['total_combinations']}")
    print(f"Summary rows: {len(summary)}")

    print(summary.to_string(index=False))

    problem = input("\nProblem name to recommend for: ").strip()

    result = FindRecommendation(summary,
                        problem,
                        l2_tolerance=1e-3,
                        norm_tolerance=1e-10,
                        energy_tolerance=None)

    print("\nTested candidates:")
    print(result["candidates"][["method", "N", "dt", "runtime",
                                "max_L2_error", "max_norm_error",
                                "passes", "reason"]].to_string(index=False))

    print("\nRecommendation:")
    if result["best"] is None:
        print("No tested candidate meets all requirements.")
    else:
        print(result["best"].to_string())

    print("\nBest qualifying result per solver:")
    for method, best in result["best_by_method"].items():
        if best is None:
            print(f"{method}: no qualifying candidate")
        else:
            print(f"{method}: N={best['N']}, dt={best['dt']:g}, runtime={best['runtime']:.6g} seconds")