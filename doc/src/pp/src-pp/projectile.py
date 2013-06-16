import odespy
import numpy as np
from math import pi, sqrt
import matplotlib.pyplot as plt

def aerodynamic_force(C, rho, A, v):
    return 0.5*C*rho*A*v**2

def forces(v_x, v_y, w, rho, A, C_D, C_L, m, g):
    # Absolute value of relative velocity
    v = sqrt((v_x - w)**2 + v_y**2)
    # Tangent vector (a, b)
    v_norm = sqrt(v_x**2 + v_y**2)
    a = v_x/v_norm
    b = v_y/v_norm
    i_t_x = a
    i_t_y = b
    # Normal vector
    if a > 0:
        i_n_x = -b
        i_n_y = a
    else:
        i_n_x = b
        i_n_y = -a

    drag_x = - aerodynamic_force(C_D, rho, A, v)*i_t_x
    drag_y = - aerodynamic_force(C_D, rho, A, v)*i_t_y
    lift_x = aerodynamic_force(C_L, rho, A, v)*i_n_x
    lift_y = aerodynamic_force(C_L, rho, A, v)*i_n_y
    gravity = -m*g
    return drag_x + lift_x, drag_y + lift_y + gravity

class Problem:
    def __init__(self, m, R, drag=True, spinrate=0, w=0):
        self.m, self.R, self.drag, self.spinrate, self.w = \
                m, R, drag, spinrate, w
        self.g = 9.81
        self.A = pi*R**2
        self.rho = 1.1184
        self.C_D = 0.47 if drag else 0
        self.C_L = spinrate/500.0*0.2

        # Initial position and velocity
        self.x0 = self.y0 = 0
        self.v_x0 = self.v_y0 = 1

    def set_initial_velocity(self, v_x, v_y):
        self.v_x0 = v_x
        self.v_y0 = v_y

    def get_initial_condition(self):
        return [self.x0,
                self.v_x0,
                self.y0,
                self.v_y0]

    def rhs(self, u, t):
        x, v_x, y, v_y = u
        F_x, F_y = forces(v_x, v_y, self.w, self.rho, self.A,
                          self.C_D, self.C_L, self.m, self.g)
        m = self.m
        return [v_x, F_x/m, v_y, F_y/m]

def solver(problem, method, dt):
    ode_solver = eval('odespy.' + method)(problem.rhs)
    ode_solver.set_initial_condition(
        problem.get_initial_condition())

    def terminate(u, t, step_no):
        y = u[step_no,2]
        return y <= 0

    # Estimate time of flight (drop aerodynamic forces)
    # y = v_y0*T - 0.5*g*T**2 = 0
    T = problem.v_y0/(0.5*problem.g)
    # Add 100% to account for possible lift force and longer flight
    T = 2*T
    N = int(round(T/float(dt)))
    t = np.linspace(0, T, N+1)

    u, t = ode_solver.solve(t, terminate)
    x = u[:,0]
    y = u[:,2]

    # Compute forces
    v_x = u[:,1]
    v_y = u[:,3]
    v = np.sqrt((v_x - problem.w)**2 + v_y**2)
    p = problem
    drag_force = aerodynamic_force(p.C_D, p.rho, p.A, v)
    lift_force = aerodynamic_force(p.C_L, p.rho, p.A, v)
    gravity_force = np.zeros(x.size) - p.m*p.g

    return x, y, t, gravity_force, drag_force, lift_force

xmax = 0
ymax = 0
for dt in [0.02]:
    #for method in ['ForwardEuler', 'RK2', 'RK4']:
    method = 'RK4'
    for drag in [True, False]:
        spinrate = 50 if drag else 0
        problem = Problem(m=0.1, R=0.11, drag=drag,
                          spinrate=spinrate, w=0)
        problem.set_initial_velocity(5, 5)
        x, y, t, g, d, l = solver(problem, method, dt)
        plt.figure(1)
        plt.plot(x, y, label='drag=%s' % (drag))
        if drag:
            plt.figure(2)
            plt.plot(x, d, label='drag force')
            if spinrate:
                plt.plot(x, l, label='lift force')
            plt.plot(x, np.abs(g), label='gravity force')
        xmax = max(xmax, x.max())
        ymax = max(ymax, y.max())
plt.figure(1)
plt.axis([x[0], xmax, 0, 1.2*ymax])
plt.legend()
plt.figure(2)
plt.legend()
plt.show()
