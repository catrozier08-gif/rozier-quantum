from .core import (
    FastPlacementCostModel,
    FastLocalSearchPlacementOptimizer,
    TopologyAwareCommunityPlacement,
    InteractionGraphBuilder,
)


class StablePlacementOptimizer:
    def __init__(
        self,
        topology,
        max_refine_passes=10,
        cost_model_cls=FastPlacementCostModel
    ):
        self.topology = topology
        self.max_refine_passes = max_refine_passes
        self.cost_model = cost_model_cls(topology)

        self.initializer = TopologyAwareCommunityPlacement(topology)
        self.refiner = FastLocalSearchPlacementOptimizer(
            topology,
            self.cost_model
        )

    def optimize(self, circuit):
        interaction_graph = InteractionGraphBuilder.build(circuit)

        initial_placement = self.initializer.place(interaction_graph)

        refined_placement = self.refiner.refine(
            interaction_graph,
            initial_placement,
            max_passes=self.max_refine_passes
        )

        initial_metrics = self.cost_model.evaluate(
            interaction_graph,
            initial_placement
        )

        refined_metrics = self.cost_model.evaluate(
            interaction_graph,
            refined_placement
        )

        return {
            "interaction_graph": interaction_graph,
            "initial_placement": initial_placement,
            "refined_placement": refined_placement,
            "initial_metrics": initial_metrics,
            "refined_metrics": refined_metrics,
        }
