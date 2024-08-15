import sqlite3
import sys

from casebasedreasoner import cbr, mop
import inspect
import types
import textwrap

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

# Given a case based reasoner, export it to a sqlite database for visual inspection/experimentation
def export_cbr_sqlite(cbrinst, dbfile, extramethodnames=[]):
    # extramethodnames is a list of methods that should also be put in database, from the cbrinst class
    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()
    # Because slots vary wildly, using an E-A-V style antipattern

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cbr_methods (
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL
        )
    ''')
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

    for methodname in extramethodnames:
        method = getattr(cbrinst, methodname)
        source = inspect.getsource(method)
        cursor.execute("INSERT INTO cbr_methods (name, code) VALUES (?, ?)", (methodname, source))

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

    # For reading into Gephi
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS nodes AS
            SELECT mopid AS id, name AS label, is_core, is_default, mop_type FROM mop
    ''')
    cursor.execute('''
        CREATE VIEW IF NOT EXISTS edges AS
             SELECT mopid AS source, abstmopid AS target, 'abst' AS label, 'abst' AS hier FROM mop_abst
            UNION ALL
             SELECT mopid AS source, specmopid AS target, 'spec' AS label, 'spec' AS hier FROM mop_spec
    ''')

    conn.commit()
    conn.close()


# Construct a new case based reasoner given a sqlite database created by export_cbr_sqlite
def load_cbr_sqlite(dbfile, env, cbrclass):
    new_cbr = cbrclass(env, env.time)
    conn = sqlite3.connect(f'file:{dbfile}?mode=ro', uri=True)
    cursor = conn.cursor()

    cursor.execute("SELECT name, code FROM cbr_methods")
    for methodrow in cursor.fetchall():
        print("Inserting CBR method " + methodrow[0])
        code = methodrow[1]
        try:
            method_code = compile(code, "<string>", "exec")
        except IndentationError:
            # When it came from a method on a class...
            method_code = compile(textwrap.dedent(code), "<string>", "exec")
        local_namespace = {}
        exec(method_code, globals(), local_namespace)
        method_name = list(local_namespace.keys())[0]
        method = local_namespace[method_name]
        bound_method = types.MethodType(method, new_cbr)
        setattr(new_cbr, method_name, bound_method)

    cursor.execute("SELECT mopid, name, is_core, is_default, mop_type FROM mop ORDER BY mopid ASC")
    mopqueue = cursor.fetchall()
    remaining_insert_attempts = 4 * len(mopqueue)
    while len(mopqueue) > 0:
        remaining_insert_attempts -= 1
        if 0 == remaining_insert_attempts:
            print("Bailing. Failed to insert all mops before running out of chances")
            break

        moprow = mopqueue.pop(0)
        mopid = moprow[0]
        name = moprow[1]

        if name in new_cbr.mops:
            print("Rejecting " + name + " because it has already been loaded")
            continue

        cursor.execute('''
            SELECT m.name FROM mop_abst q
                INNER JOIN mop m ON q.abstmopid = m.mopid
                WHERE q.mopid=?
        ''', (mopid,))

        needed_mops = []
        absts = {row[0] for row in cursor.fetchall()}
        needed_mops.extend(absts)

        is_core = (moprow[2]>0)
        is_default = (moprow[3]>0)
        mop_type = moprow[4]

        cursor.execute('''SELECT slot.name AS slotname, val, is_func, mop.name AS refmopname, TYPEOF(val) AS val_type 
                               FROM slot LEFT JOIN mop ON slot.ref_mopid=mop.mopid
                               WHERE slot.mopid=?
                           ''', (mopid,))
        slotrows = cursor.fetchall()
        slotmops = [row[3] for row in slotrows if row[3] is not None]
        needed_mops.extend(slotmops)

        # Don't love this brute force approach, but it's easy and obviously-working
        missing_mops = [needed_mopname for needed_mopname in needed_mops if needed_mopname not in new_cbr.mops]
        if len(missing_mops) > 0:
            print("Requeueing " + name + " because it needs something not yet loaded")
            mopqueue.append(moprow)
            continue

        create_slots = {}
        for slotrow in slotrows:
            slotname = slotrow[0]
            slotval = slotrow[1]
            is_func = slotrow[2]
            slot_mopname = slotrow[3]
            slot_valtype = slotrow[4]

            if is_func:
                try:
                    method_code = compile(slotval, "<string>", "exec")
                except IndentationError:
                    # When it came from a method on a class...
                    method_code = compile(textwrap.dedent(slotval), "<string>", "exec")
                local_namespace = {}
                exec(method_code, globals(), local_namespace)
                method_name = list(local_namespace.keys())[0]
                method = local_namespace[method_name]
                bound_method = types.MethodType(method, new_cbr)
                setattr(new_cbr, method_name, bound_method)
                create_slots[slotname] = bound_method
            elif slot_mopname is not None:
                # print("Looking up mop " + slot_mopname + " for " + slotname + " on mop " + name)
                mopref = new_cbr.mops[slot_mopname]
                create_slots[slotname] = mopref
            else:
                # SQLite's type system lets us get away with this
                if slot_valtype == 'text':
                    create_slots[slotname] = slotval
                elif slot_valtype == 'integer':
                    create_slots[slotname] = int(slotval)
                elif slot_valtype == 'real':
                    create_slots[slotname] = float(slotval)
                else:
                    sys.stderr.write(f"Error! Do not know how to interpret \"{slotval}\" as a {slot_valtype}\n")

        new_cbr.add_mop(name, absts=absts, mop_type=mop_type, slots=create_slots,
                        is_default_mop=is_default, is_core_cbr_mop=is_core)
        print("Loaded mop " + name + ", there are " + str(len(mopqueue)) + " mops left")
    return new_cbr


