import multiprocessing

import pulp

num_cores = multiprocessing.cpu_count()
problem = pulp.LpProblem('LP', pulp.LpMaximize)

x = pulp.LpVariable('x', cat='Integer')
y = pulp.LpVariable('y', cat='Integer')

problem += 1 * x + 3 * y <= 30
problem += 2 * x + 1 * y <= 40
problem += x >= 0
problem += y >= 0
problem.objective = x + 2 * y

solver = pulp.SCIP_CMD()
status = problem.solve(solver)

print('Status:', pulp.LpStatus[status])
print('x=', x.value(), 'y=', y.value(), 'obj=', problem.objective.value())
