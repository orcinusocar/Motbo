from pathlib import Path

from app.simulation.simulator import Simulator


def test_step_advances_time(example_model: Path) -> None:
    sim = Simulator(example_model, timestep=0.002)
    sim.reset(seed=1)
    assert sim.time == 0.0
    sim.step()
    assert abs(sim.time - sim.timestep) < 1e-9


def test_reset_is_deterministic(example_model: Path) -> None:
    sim = Simulator(example_model)
    sim.reset(seed=7)
    first = sim.snapshot()
    sim.step()
    sim.reset(seed=7)
    second = sim.snapshot()
    assert (first["qpos"] == second["qpos"]).all()
