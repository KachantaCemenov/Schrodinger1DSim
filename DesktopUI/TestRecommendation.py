from Recommendation import BuildRecommendationSummary


if __name__ == "__main__":
    folder = input("Saved benchmark run folder: ").strip().strip('"')

    manifest, summary = BuildRecommendationSummary(folder)

    print(f"\nCompleted combinations: {manifest['completed_combinations']} / {manifest['total_combinations']}")
    print(f"Summary rows: {len(summary)}")

    print(summary.to_string(index=False))