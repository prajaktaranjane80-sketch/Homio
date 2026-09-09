def blast_radius(report):
    return tuple(sorted(set(report.impacted_paths)))
