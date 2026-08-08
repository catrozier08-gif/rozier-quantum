
import networkx as nx
import time
from rozier.auto_fixer import RozierAutoFixer

def test_empty():
    G = nx.Graph()
    fixer = RozierAutoFixer()
    result = fixer.fix_quantum(G, triggered_codes=["Q-007"], execute=True)
    assert result['pre_stress'] == 0

def test_small_executes():
    G = nx.Graph()
    G.add_edges_from([(0,1),(1,2)])
    fixer = RozierAutoFixer()
    result = fixer.fix_quantum(G, chip_size=2, num_chips=2, triggered_codes=["Q-007","Q-008"], execute=True)
    assert result['reduction_pct'] >= 0

def test_20q():
    import random
    random.seed(0)
    G = nx.Graph()
    G.add_nodes_from(range(20))
    for _ in range(40):
        u = random.randint(0,19)
        v = random.randint(0,19)
        if u!=v:
            G.add_edge(u,v)
    fixer = RozierAutoFixer()
    result = fixer.fix_quantum(G, chip_size=5, num_chips=4, triggered_codes=["Q-007"], execute=True)
    assert result['reduction_pct'] >= 0

def test_100k_thorough():
    for n in [1000, 10000, 100000]:
        G = nx.Graph()
        G.add_nodes_from(range(n))
        for i in range(n-1):
            G.add_edge(i, i+1)
        fixer = RozierAutoFixer()
        start = time.time()
        result = fixer.fix_quantum(G, chip_size=34, num_chips=max(1,n//34), triggered_codes=["Q-007"], execute=True)
        elapsed = time.time() - start
        assert elapsed < 5.0
        assert result['reduction_pct'] >= 0

def test_refiner_toolbags():
    from rozier.refiner import RefinementEngine
    circuit = nx.Graph()
    circuit.add_nodes_from(range(10))
    for i in range(9):
        circuit.add_edge(i,i+1)
    topo = nx.Graph()
    topo.add_nodes_from(range(10))
    for i in range(9):
        topo.add_edge(i,i+1)
    health = {0: ["Q-001"]}
    report = {'interaction_graph': circuit, 'topology_graph': topo, 'health_report': health}
    refiner = RefinementEngine(report)
    bags = refiner.pack_toolbags()
    gravity = refiner.generate_gravity_map()
    assert len(bags)>0
    assert len(gravity)>0
