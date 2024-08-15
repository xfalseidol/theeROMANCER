import sqlite3
import inspect

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
    g.append("penwidth=3")
    g.extend(default_mop_nodes)

    g.append("  subgraph clusterCore {")
    g.append("  label=\"Core MOPs\"")
    g.append("  penwidth=3")
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

def export_cbr_sqlite(cbrinst, dbfile):
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    # Because slots vary wildly, using an E-A-V style antipattern

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_type (
            mop_type TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute("INSERT INTO mop_type (mop_type) VALUES ('instance'), ('mop')")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop (
            mopid INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_core BOOLEAN NOT NULL,
            is_default BOOLEAN NOT NULL,
            mop_type TEXT NOT NULL REFERENCES mop_type(mop_type),
            UNIQUE(name)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_abst (
            id INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            abstmopid INTEGER NOT NULL REFERENCES mop(mopid),
            UNIQUE(mopid, abstmopid)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mop_spec (
            id INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            specmopid INTEGER NOT NULL REFERENCES mop(mopid),
            UNIQUE(mopid, specmopid)
        )
    ''')
    # Take advantage of SQLite's type system. Can insert things of any type into the value column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slot (
            id INTEGER PRIMARY KEY,
            mopid INTEGER NOT NULL REFERENCES mop(mopid),
            name TEXT NOT NULL,
            val NUMBER NOT NULL,
            ref_mopid INTEGER REFERENCES mop(mopid),
            is_func BOOLEAN NOT NULL
        )
    ''')

    # Insert all MOPs first. Relationships will be set up later
    for mopname in cbrinst.mops:
        # print("Nodes for " + str(mopname))
        this_mop = cbrinst.mops[mopname]
        cursor.execute("INSERT INTO mop(name, is_core, is_default, mop_type) VALUES (?, ?, ?, ?)",
                       (this_mop.mop_name, this_mop.is_core_cbr, this_mop.is_default, this_mop.mop_type))
    conn.commit()

    for mopname in cbrinst.mops:
        # Yes, all the subselects are slow. If it turns out to matter, can grab the lot later
        this_mop = cbrinst.mops[mopname]
        abstrows = [(this_mop.mop_name, abst.mop_name) for abst in this_mop.absts]
        cursor.executemany("INSERT INTO mop_abst(mopid, abstmopid) VALUES"
                           " ((SELECT mopid FROM mop WHERE name=?), (SELECT mopid FROM mop WHERE name=?))", abstrows)

        specrows = [(this_mop.mop_name, spec.mop_name) for spec in this_mop.specs]
        cursor.executemany("INSERT INTO mop_spec(mopid, specmopid) VALUES"
                           " ((SELECT mopid FROM mop WHERE name=?), (SELECT mopid FROM mop WHERE name=?))", specrows)

        for slotname in this_mop.slots:
            val = this_mop.slots[slotname]
            val_s = str(val)
            is_func = False
            if callable(val):
                try:
                    val_s = inspect.getsource(val)
                except OSError as e:
                    print(f"Source for {slotname} unavailable")
                    val_s = None
                is_func = True

            cursor.execute("INSERT INTO slot(mopid, name, val, ref_mopid, is_func) VALUES"
                           " ((SELECT mopid FROM mop WHERE name=?), ?, ?, (SELECT mopid FROM mop WHERE name=?), ?)",
                           (this_mop.mop_name, slotname, val_s, val_s, is_func))

    conn.commit()
    conn.close()
