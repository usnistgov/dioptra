import yaml
from pprint import pprint
from dioptra.task_engine import validation

# here is a sample YAML document with a swappable task called "attack" defined.
# The swap has two tasks which can be selected: "attack1" or "attack2"

"""
load_model:
  model:
    name: $name
attack_step:
  ?attack:
    attack1:
      model: $model
      epsilon: $eps
    attack2:
      model: $model
      epsilon: $eps
      iterations: $n
"""

# I chose '?' as an indicator for a swap task because YAML will treat it as the first
# character in the key and can be interpreted as a question: "which task do you want?"

# Note: After reading up on the YAML spec I found that '? ' (question mark followed by a
# space) actually denotes a "complex mapping key" in YAML. So it's possible it could
# lead to confusion. An alternative is '^' (carrot), which I think is unused by YAML.

# I made it so anchors and aliases are not part of our swappable graph spec. There
# isn't anything you can't write out manually as they are basically a convenience to
# copy and paste a block of YAML. We still need the ability to select from the
# dictionary of swaps either way. I did include two examples of how anchors could be
# optionally used to re-use components of the YAML. The first example shows how they can
# be used for common params (this can be seen as an argument for not implementing our
# spec for this feature). The second shows how you could specify your swap options up
# front, which could then be used in multiple places. Note that the anchor has to be
# specified before it is aliased in the YAML document. All three examples should be
# equivalent.

# I added a fourth example to demonstrate multiple swaps.


def render(graph, swaps):
    rendered_graph = {}
    for step, task in graph.items():
        if step.startswith("_"):
            continue

        rendered_graph[step] = {}
        for task_name, task_defn in task.items():
            if task_name.startswith("?"):
                task_name = swaps[task_name[1:]]  # could raise swap not specified error
                swap = task_defn[task_name]
                rendered_graph[step][task_name] = swap
            else:
                rendered_graph[step][task_name] = graph[step][task_name]

    return rendered_graph


def validate(graph):
    # validation checks that can be performed with only the graph portion of the yaml
    issues = []
    issues += validation._find_non_string_keys(graph, "graph")
    issues += validation._check_graph_dependencies({"graph": graph})
    issues += validation._check_step_structure({"graph": graph})
    return issues


def main():
    print("-----------------------------------------------------------")
    data = """
    load_model:
      model:
        name: $name
    attack_step:
      ?attack:
        attack1:
          model: $model
          epsilon: $eps
        attack2:
          model: $model
          epsilon: $eps
          iterations: $n
    """

    graph = yaml.safe_load(data)
    # pprint(graph)

    swaps = {"attack": "attack1"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    swaps = {"attack": "attack2"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    print("-----------------------------------------------------------")
    data = """
    load_model:
      model:
        name: $name
    attack_step:
      ?attack:
        _: &common_attack_params
          model: $model
          epsilon: $eps
        attack1: *common_attack_params
        attack2:
          <<: *common_attack_params
          iterations: $n
    """

    graph = yaml.safe_load(data)
    # pprint(graph)

    swaps = {"attack": "attack1"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    swaps = {"attack": "attack2"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    print("-----------------------------------------------------------")
    data = """
    _: # need to make sure task engine skips
      attack: &attack_swap_options
        attack1:
          model: $model
          epsilon: $eps
        attack2:
          model: $model
          epsilon: $eps
          iterations: $n
    load_model:
      model:
        name: $name
    attack_step:
      ?attack: *attack_swap_options
    """

    graph = yaml.safe_load(data)
    # pprint(graph)

    swaps = {"attack": "attack1"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    swaps = {"attack": "attack2"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)

    print("-----------------------------------------------------------")
    data = """
    load_model:
      model:
        name: $name
    attack_step:
      ?attack:
        attack1:
          model: $model
          epsilon: $eps
        attack2:
          model: $model
          epsilon: $eps
          iterations: $n
    defense_step:
      ?defense:
        defense1:
        defense2:
          strength: $strength
        defense3:
          strength: 4
    """

    graph = yaml.safe_load(data)
    # pprint(graph)

    swaps = {"attack": "attack1", "defense": "defense3"}
    rendered_graph = render(graph, swaps)
    pprint(rendered_graph)
    issues = validate(rendered_graph)
    print("issues:", issues)


if __name__ == "__main__":
    main()
