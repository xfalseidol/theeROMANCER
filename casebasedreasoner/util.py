
def make_graphviz_graph(cbrinst, include_inheritance_edges=True, include_slot_edges=True):
    ''' Given a CBR, returns a representation of this in graphviz format '''
    g = ["digraph G {", "splines=true", "overlap=false"]
    mopname_to_nodename = {}
    curr_nodeid = 0
    moptype_to_color = {"mop": "red", "instance": "green"}

    for mopname in cbrinst.mops:  # Generate graphviz table ids first
        curr_nodename = "n" + str(curr_nodeid)
        mopname_to_nodename[mopname] = curr_nodename
        curr_nodeid += 1

    slot_edges = []
    core_mop_nodes = []
    default_mop_nodes = []
    non_default_mop_nodes = []

    for mopname in cbrinst.mops:
        # print("Nodes for " + str(mopname))
        this_mop = cbrinst.mops[mopname]
        curr_nodename = mopname_to_nodename[mopname]

        thismop_color = moptype_to_color[this_mop.mop_type]
        thislabel = [
            f"<table cellspacing=\"0\" bgcolor=\"{thismop_color}\"><tr><td colspan=\"2\" id=\"n\">{str(mopname)}</td></tr>"]
        slotnum = 0
        for slotname in this_mop.slots:
            val = this_mop.slots[slotname]
            val_s = "lambda" if callable(val) else str(val)
            slotnum = slotnum + 1
            thislabel.append(f"<tr><td>{slotname}</td><td id=\"s{str(slotnum)}\">{val_s}</td></tr>")
            if val_s in mopname_to_nodename:
                slot_edges.append(
                    f" {curr_nodename}:s{str(slotnum)} -> {mopname_to_nodename[val_s]}:n [color=\"black\"]")

        thislabel.append(f"</table>")
        l = "".join(thislabel)

        if this_mop.is_core_cbr_mop():
            core_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")
        if this_mop.is_default_mop():
            default_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")
        else:
            non_default_mop_nodes.append(f"{curr_nodename} [shape=none label=<{l}>];")

    g.append("subgraph clusterDefault {")
    g.append("label=\"Default MOPs\"")
    g.extend(default_mop_nodes)

    g.append("  subgraph clusterCore {")
    g.append("  label=\"Core MOPs\"")
    g.extend(core_mop_nodes)
    g.append("  }")

    g.append("}")

    g.extend(non_default_mop_nodes)
    if include_inheritance_edges:
        for mopname in cbrinst.mops:
            # print("Edges for " + str(mopname))
            this_mop = cbrinst.mops[mopname]
            nodename = mopname_to_nodename[mopname]
            for abst in this_mop.absts:
                if abst.mop_name not in mopname_to_nodename:
                    print("Weird. No node named " + abst.mop_name)
                    continue
                # print(f"    abst {abst}")
                g.append(f" {nodename}:n -> {mopname_to_nodename[abst.mop_name]}:n [color=\"orange\"]")
            for spec in this_mop.specs:
                if spec.mop_name not in mopname_to_nodename:
                    print("Weird. No node named " + spec.mop_name)
                    continue
                # print(f"    spec {spec}")
                g.append(f" {nodename}:n -> {mopname_to_nodename[spec.mop_name]}:n [color=\"blue\"]")

    if include_slot_edges:
        g.append("\n".join(slot_edges))

    g.append('}')
    return "\n".join(g)
