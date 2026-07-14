# Visualization: Pareto front plots, supply chain flow diagrams, and sensitivity analysis charts for dual-objective results.
import matplotlib.pyplot as plt

def pareto_front(pareto):
    points = sorted(set(pareto))       # pareto = [(cost, SR), ...]; drop repeated points
    costs, srs = zip(*points)

    fig, ax = plt.subplots()
    ax.set_xlabel('supply risk SR_norm [–]')
    ax.set_ylabel('total cost [€]')
    ax.grid(True)
    ax.scatter(srs, costs)             # markers only: a MILP front may have gaps -> never interpolate
    return fig, ax