from flask import Flask, render_template, request, redirect, url_for, session 
import os, json
from werkzeug.utils import secure_filename
import pandas as pd
import pulp

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "1234"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

def pareto_frontier(projects, step=100, weights=None):
    if weights is None:
        weights = {"rc": 1.0, "wt": 0.4, "roi": 0.4}
    costs = [int(round(sum(p["BudgetRequest"].values()))) for p in projects]
    rc_v  = [weights["rc"]  * p["RCSaving"] for p in projects]
    wt_v  = [weights["wt"]  * p["Weight"]   for p in projects]
    roi_v = [weights["roi"] * p["ROI"]      for p in projects]
    maxB = sum(costs)
    dp = [(0, 0, 0, 0) for _ in range(maxB + 1)]
    for c, rv, wv, ov in zip(costs, rc_v, wt_v, roi_v):
        for b in range(maxB, c - 1, -1):
            tot, r_sum, w_sum, o_sum = dp[b - c]
            cand = tot + (rv + wv + ov)
            if cand > dp[b][0]:
                dp[b] = (cand, r_sum + rv, w_sum + wv, o_sum + ov)
    frontier = []
    best = -1
    for B in range(0, maxB + 1, step):
        tot, rs, ws, osum = dp[B]
        if tot > best:
            remB = B
            chosen = []
            for i in range(len(costs) - 1, -1, -1):
                c = costs[i]
                v = rc_v[i] + wt_v[i] + roi_v[i]
                if remB >= c and dp[remB - c][0] + v == dp[remB][0]:
                    chosen.append(projects[i]["NomProjet"])
                    remB -= c
            frontier.append({
                "budget": B,
                "benefit": tot,
                "rc": round(rs, 2),
                "wt": round(ws, 2),
                "roi": round(osum, 2),
                "projects": chosen
            })
            best = tot
    return frontier

def run_dynamic_scenario(df_projects, available_budgets, scenario_def, objective_2025=0):
    df_local = df_projects.copy()
    criteria = scenario_def.get("criteria", [])
    scenario_custom_name = scenario_def.get("name", "").strip()

    max_priority = max(crit["priority"] for crit in criteria) if criteria else 1
    scenario_label = ", ".join(crit["param"] for crit in sorted(criteria, key=lambda c: c["priority"])) if criteria else "RC Saving"
    if scenario_custom_name:
        scenario_label = scenario_custom_name

    norm_RCSaving = df_local["RCSaving"].max() if df_local["RCSaving"].max() > 0 else 1
    norm_Weight = df_local["Weight"].max() if df_local["Weight"].max() > 0 else 1
    norm_ROI = df_local["ROI"].max() if df_local["ROI"].max() > 0 else 1

    prob = pulp.LpProblem("Portfolio_dynamic", pulp.LpMaximize)
    decision_vars = {idx: pulp.LpVariable(f"x_{idx}", cat="Binary") for idx in df_local.index}

    obj_expr = 0
    for crit in criteria:
        coeff = (max_priority + 1 - crit["priority"])
        param = crit["param"]
        if param == "RC Saving":
            term = pulp.lpSum((df_local.loc[i, "RCSaving"] / norm_RCSaving) * decision_vars[i] for i in df_local.index)
        elif param == "Weight":
            term = - pulp.lpSum((df_local.loc[i, "Weight"] / norm_Weight) * decision_vars[i] for i in df_local.index)
        elif param == "ROI":
            term = - pulp.lpSum((df_local.loc[i, "ROI"] / norm_ROI) * decision_vars[i] for i in df_local.index)
        else:
            continue
        obj_expr += coeff * term

    prob += obj_expr, "DynamicObjective"

    for bc in available_budgets:
        constraint = pulp.lpSum(df_local.loc[i, bc] * decision_vars[i] for i in df_local.index)
        prob += (constraint <= available_budgets[bc]), f"Budget_{bc}"

    if any(crit["param"] == "ROI" for crit in criteria) and not (len(criteria) == 1 and criteria[0]["param"] == "ROI"):
        for i in df_local.index:
            if df_local.loc[i, "ROI"] == 0:
                prob += decision_vars[i] == 0, f"NoZeroROI_{i}"

    if "Obligatoire" in df_local.columns:
        for idx, row in df_local.iterrows():
            if row["Obligatoire"]:
                prob += decision_vars[idx] == 1, f"Mandatory_{idx}"

    prob.solve()
    status = pulp.LpStatus[prob.status]

    selected_projects = []
    for idx in df_local.index:
        if pulp.value(decision_vars[idx]) == 1:
            rowp = df_local.loc[idx]
            nom_projet = rowp.get("Nom du Projet", "")
            change_req = rowp.get("Change Request", "")
            title = rowp.get("Title", "")
            combined_name = nom_projet
            if change_req or title:
                combined_name += f" (CR: {change_req}) - {title}"
            if rowp.get("Obligatoire", False):
                combined_name += " <span class='badge badge-primary'>Prioritaire</span>"
            selected_projects.append({
                "idx": idx,
                "NomProjet": combined_name,
                "RCSaving": float(rowp["RCSaving"]),
                "Weight": float(rowp["Weight"]),
                "ROI": round(float(rowp["ROI"])),
                "BudgetRequest": {bc: float(rowp[bc]) for bc in available_budgets},
                "Obligatoire": bool(rowp.get("Obligatoire", False))
            })
    non_selected_projects = []
    for idx in df_local.index:
        if pulp.value(decision_vars[idx]) != 1:
            row = df_local.loc[idx]
            def clean(val):
                return str(val).strip() if pd.notna(val) else None

            non_selected_projects = []
            for idx in df_local.index:
                if pulp.value(decision_vars[idx]) != 1:
                    row = df_local.loc[idx]
                    nom_projet = (
                        clean(row.get("Nom du Projet")) or
                        clean(row.get("NomProjet")) or
                        clean(row.get("Title")) or
                        None
                    )
                    rc = float(row["RCSaving"])
                    weight = float(row["Weight"])
                    roi = float(row["ROI"])

                    if nom_projet or rc > 0 or weight != 0 or roi > 0:
                        non_selected_projects.append({
                            "idx": idx,
                            "NomProjet": nom_projet or "Projet sans nom",
                            "RCSaving": rc,
                            "Weight": weight,
                            "ROI": roi,
                            "BudgetRequest": {bc: float(row[bc]) for bc in available_budgets},
                            "Obligatoire": bool(row.get("Obligatoire", False))
                        })





    def sort_key(p):
        key = [0 if p["Obligatoire"] else 1]
        for crit in sorted(criteria, key=lambda c: c["priority"]):
            if crit["param"] == "RC Saving":
                key.append(-p["RCSaving"])
            elif crit["param"] == "Weight":
                key.append(p["Weight"])
            elif crit["param"] == "ROI":
                key.append(p["ROI"])
        return tuple(key)

    selected_projects = sorted(selected_projects, key=sort_key)
    total_rc = sum(p["RCSaving"] for p in selected_projects)
    total_weight = sum(p["Weight"] for p in selected_projects)
    total_roi = sum(p["ROI"] for p in selected_projects)
    budget_used = {bc: sum(p["BudgetRequest"][bc] for p in selected_projects) for bc in available_budgets}

    target_results = []
    for crit in criteria:
        param = crit["param"]
        target_val = crit.get("target", None)
        if target_val is not None:
            actual_val = 0
            if param == "RC Saving":
                actual_val = total_rc
            elif param == "Weight":
                actual_val = total_weight
            elif param == "ROI":
                actual_val = total_roi
            met = (actual_val >= target_val) if param == "RC Saving" else (actual_val <= target_val)
            target_results.append({
                "param": param,
                "target": target_val,
                "achieved": actual_val,
                "status": "met" if met else "not_met"
            })

    scenario_data = {
        "criteria": criteria,
        "scenario_label": scenario_label,
        "status": status,
        "selected_projects": selected_projects,
        "total_rc": total_rc,
        "total_weight": total_weight,
        "total_roi": total_roi,
        "budget_used": budget_used,
        "targets": target_results,
        "non_selected_projects": non_selected_projects

    }
    return scenario_data


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Aucun fichier envoyé."
    file = request.files['file']
    if file.filename == '':
        return "Aucun fichier sélectionné."
    if not allowed_file(file.filename):
        return "Extension de fichier non autorisée."
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Récupération du JSON des scénarios (créé côté index)
    scenarios_json = request.form.get('scenarios')
    try:
        scenario_defs = json.loads(scenarios_json) if scenarios_json else []
    except Exception as e:
        print("Erreur lors du parsing des scénarios :", e)
        scenario_defs = []
    if not scenario_defs:
        scenario_defs = [{"criteria": [{"param": "RC Saving", "priority": 1}]}]
    
    # Lecture de l'Excel (en supposant header=5)
    try:
        df = pd.read_excel(file_path, header=5)
    except Exception as e:
        print("Erreur de lecture Excel:", e)
        return "Impossible de lire l'Excel."
    
    print("DEBUG: Fichier Excel lu, shape df =", df.shape)
    print("DEBUG: Colonnes initiales df =", df.columns.tolist())
    
    df.columns = df.columns.str.strip().str.replace("'", "", regex=False)
    col_first = df.iloc[:, 0].astype(str).str.lower().str.strip()
    objectif_mask = col_first.str.contains("objectif")
    budget_mask = col_first.str.contains("available budget")
    
    print("DEBUG: objectif_mask.any() =", objectif_mask.any())
    print("DEBUG: budget_mask.any() =", budget_mask.any())
    
    if not objectif_mask.any():
        return "Impossible de trouver 'Objectif' dans la première colonne."
    if not budget_mask.any():
        return "Impossible de trouver 'Available budget' dans la première colonne."
    
    objectif_idx = df.index[objectif_mask][0]
    available_idx = df.index[budget_mask][0]
    start_projects = df.index[0]
    df_projects = df.loc[start_projects:objectif_idx - 1].copy()
    row_objectif = df.loc[objectif_idx]
    row_available = df.loc[available_idx]
    
    print("DEBUG: objectif_idx =", objectif_idx, "; available_idx =", available_idx, "; start_projects =", start_projects)
    print("DEBUG: shape df_projects =", df_projects.shape)
    print("DEBUG: Aperçu df_projects (5 premières lignes) :\n", df_projects.head(5))
    
    # Filtrage : suppression des lignes dont "Nom du Projet" est NaN
    if "Nom du Projet" in df_projects.columns:
        before_drop = df_projects.shape[0]
        df_projects = df_projects[df_projects["Nom du Projet"].notna()]
        after_drop = df_projects.shape[0]
        print(f"DEBUG: Lignes avant filtrage = {before_drop}; après filtrage (Nom du Projet not NaN) = {after_drop}")
    
    def is_budget_col(c):
        return "budget" in str(c).lower() and "previous" not in str(c).lower()
    col_names = list(df_projects.columns)
    budget_cols = [c for c in col_names if is_budget_col(c)]
    
    objective_2025 = 0
    col_2025 = None
    for c in budget_cols:
        if "2025" in str(c):
            col_2025 = c
            break
    if col_2025:
        val_obj = row_objectif.get(col_2025, 0)
        if pd.notna(val_obj):
            objective_2025 = float(val_obj)
    print("DEBUG: objective_2025 =", objective_2025)
    
    available_budgets = {}
    for c in budget_cols:
        val = row_available.get(c, 0)
        if pd.isna(val):
            val = 0
        available_budgets[c] = float(val)
    print("DEBUG: available_budgets =", available_budgets)
    
    rename_map = {
        "RC saving k€": "RCSaving",
        "RC saving keuros": "RCSaving",
        "RC saving": "RCSaving",
        "Weight impact kg": "Weight",
        "Weight impact": "Weight",
        "Weight": "Weight",
    }
    df_projects.rename(columns=rename_map, inplace=True)
    print("DEBUG: Colonnes après rename:", df_projects.columns.tolist())
    
    if "Obligatoire" in df_projects.columns:
        df_projects["Obligatoire"] = df_projects["Obligatoire"].astype(str).str.strip().str.lower() == "true"
    if "ROI" not in df_projects.columns:
        df_projects["ROI"] = 0.0
    
    for col_to_float in ["RCSaving", "Weight", "ROI"]:
        if col_to_float in df_projects.columns:
            df_projects[col_to_float] = pd.to_numeric(df_projects[col_to_float], errors='coerce').fillna(0)
    for bc in budget_cols:
        df_projects[bc] = pd.to_numeric(df_projects[bc], errors='coerce').fillna(0)
    
    print("DEBUG: shape final df_projects =", df_projects.shape)
    print("DEBUG: Aperçu final df_projects:\n", df_projects.head(5))
    
    scenarios_data = {}
    for idx, scen_def in enumerate(scenario_defs, start=1):
        key = f"scenario{idx}"
        print("\n========== DEBUG: Lancement scénario", key, "==========")
        scenarios_data[key] = run_dynamic_scenario(df_projects, available_budgets, scen_def, objective_2025)
        w = {"rc": 1.0, "wt": 1.0, "roi": 1.0}
        for crit in scen_def.get("criteria", []):
            if crit["param"] == "RC Saving": w["rc"] = crit.get("weight", 1.0)
            if crit["param"] == "Weight":    w["wt"] = crit.get("weight", 1.0)
            if crit["param"] == "ROI":       w["roi"] = crit.get("weight", 1.0)

        all_projects = [p for p in scenarios_data[key]["selected_projects"] if "BudgetRequest" in p]
        scenarios_data[key]["opt_curve"] = pareto_frontier(all_projects, step=100, weights=w)
        
    
    return render_template("multiscenario_report.html",
                           scenarios_data=scenarios_data,
                           budget_cols=budget_cols,
                           available_budgets=available_budgets)

@app.route('/explanation')
def explanation():
    return "Page d'explication... (à adapter)"

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
