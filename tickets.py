#!/usr/bin/env python3
"""
╔══════════════════════════════════════╗
║        CLI TICKETSYSTEM v1.0         ║
╚══════════════════════════════════════╝
"""

import json
import os
import sys
import datetime
import argparse
from pathlib import Path

# ─── Farben & Styles ────────────────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN="\033[42m"
    BG_BLUE= "\033[44m"

def bold(s):    return f"{C.BOLD}{s}{C.RESET}"
def dim(s):     return f"{C.DIM}{s}{C.RESET}"
def red(s):     return f"{C.RED}{s}{C.RESET}"
def green(s):   return f"{C.GREEN}{s}{C.RESET}"
def yellow(s):  return f"{C.YELLOW}{s}{C.RESET}"
def blue(s):    return f"{C.BLUE}{s}{C.RESET}"
def cyan(s):    return f"{C.CYAN}{s}{C.RESET}"
def magenta(s): return f"{C.MAGENTA}{s}{C.RESET}"

# ─── Konfiguration ──────────────────────────────────────────────────────────

DATA_FILE = Path.home() / ".tickets.json"

PRIORITIES = {
    "kritisch": ("🔴", C.RED),
    "hoch":     ("🟠", C.YELLOW),
    "mittel":   ("🟡", C.CYAN),
    "niedrig":  ("🟢", C.GREEN),
}

STATUSES = {
    "offen":       ("○", C.YELLOW),
    "in_arbeit":   ("◑", C.BLUE),
    "wartet":      ("◷", C.MAGENTA),
    "gelöst":      ("●", C.GREEN),
    "geschlossen": ("✕", C.DIM),
}

CATEGORIES = ["bug", "feature", "aufgabe", "frage", "sonstiges"]

# ─── Datenverwaltung ─────────────────────────────────────────────────────────

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"tickets": {}, "next_id": 1}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def fmt_priority(p):
    icon, color = PRIORITIES.get(p, ("?", C.WHITE))
    return f"{color}{icon} {p}{C.RESET}"

def fmt_status(s):
    icon, color = STATUSES.get(s, ("?", C.WHITE))
    return f"{color}{icon} {s}{C.RESET}"

def fmt_category(c):
    colors = {"bug": C.RED, "feature": C.BLUE, "aufgabe": C.CYAN,
              "frage": C.MAGENTA, "sonstiges": C.WHITE}
    color = colors.get(c, C.WHITE)
    return f"{color}[{c}]{C.RESET}"

def ticket_id_str(tid):
    return bold(cyan(f"#{tid}"))

def separator(char="─", width=60):
    return dim(char * width)

def header(title):
    w = 60
    print(f"\n{C.BOLD}{C.BLUE}╔{'═'*(w-2)}╗")
    print(f"║{title.center(w-2)}║")
    print(f"╚{'═'*(w-2)}╝{C.RESET}")

def choose(prompt, options, default=None):
    """Interaktive Auswahl."""
    for i, o in enumerate(options, 1):
        print(f"  {dim(str(i)+'.')} {o}")
    default_hint = f" [{default}]" if default else ""
    while True:
        val = input(f"\n{prompt}{default_hint}: ").strip()
        if not val and default:
            return default
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val)-1]
        if val in options:
            return val
        print(red("  ✗ Ungültige Auswahl."))

def prompt(label, default=None, required=True):
    hint = f" [{default}]" if default else ""
    while True:
        val = input(f"{label}{hint}: ").strip()
        if not val and default:
            return default
        if val or not required:
            return val
        print(red("  ✗ Pflichtfeld."))

# ─── Ticket-Operationen ──────────────────────────────────────────────────────

def cmd_neu(args, data):
    """Neues Ticket erstellen."""
    header("  NEUES TICKET ERSTELLEN  ")

    title = prompt(bold("Titel"))
    print(f"\n{bold('Beschreibung')} {dim('(leer lassen zum Überspringen)')}")
    desc = prompt("", required=False)
    
    print(f"\n{bold('Priorität')}")
    prio = choose("Auswahl", list(PRIORITIES.keys()), "mittel")
    
    print(f"\n{bold('Kategorie')}")
    cat = choose("Auswahl", CATEGORIES, "aufgabe")

    tid = str(data["next_id"])
    data["tickets"][tid] = {
        "id": tid,
        "title": title,
        "description": desc,
        "priority": prio,
        "category": cat,
        "status": "offen",
        "created": now(),
        "updated": now(),
        "comments": [],
    }
    data["next_id"] += 1
    save_data(data)

    print(f"\n{green('✓')} Ticket {ticket_id_str(tid)} erstellt: {bold(title)}")

def cmd_liste(args, data):
    """Tickets auflisten."""
    tickets = list(data["tickets"].values())
    
    # Filter
    if args.status:
        tickets = [t for t in tickets if t["status"] == args.status]
    if args.prioritaet:
        tickets = [t for t in tickets if t["priority"] == args.prioritaet]
    if args.kategorie:
        tickets = [t for t in tickets if t["category"] == args.kategorie]
    if args.suche:
        q = args.suche.lower()
        tickets = [t for t in tickets
                   if q in t["title"].lower() or q in t.get("description","").lower()]

    if not tickets:
        print(f"\n{yellow('ℹ')} Keine Tickets gefunden.")
        return

    header(f"  TICKETS ({len(tickets)})  ")
    
    # Sortierung
    sort_key = {"prioritaet": "priority", "status": "status",
                "datum": "created", "id": "id"}.get(args.sortierung, "id")
    tickets.sort(key=lambda t: t.get(sort_key, ""))

    for t in tickets:
        cmt_count = len(t.get("comments", []))
        cmt_hint = dim(f" 💬{cmt_count}") if cmt_count else ""
        print(
            f"  {ticket_id_str(t['id']).ljust(14)}"
            f" {fmt_status(t['status']).ljust(30)}"
            f" {fmt_priority(t['priority']).ljust(30)}"
            f" {fmt_category(t['category'])}"
            f"{cmt_hint}"
        )
        print(f"    {bold(t['title'])}")
        print(f"    {dim(t['created'])}")
        print(separator())

def cmd_zeige(args, data):
    """Ticket-Details anzeigen."""
    t = data["tickets"].get(str(args.id))
    if not t:
        print(red(f"✗ Ticket #{args.id} nicht gefunden."))
        return

    header(f"  TICKET #{t['id']}  ")
    print(f"  {bold('Titel')}      {t['title']}")
    print(f"  {bold('Status')}     {fmt_status(t['status'])}")
    print(f"  {bold('Priorität')}  {fmt_priority(t['priority'])}")
    print(f"  {bold('Kategorie')}  {fmt_category(t['category'])}")
    print(f"  {bold('Erstellt')}   {dim(t['created'])}")
    print(f"  {bold('Geändert')}   {dim(t['updated'])}")
    
    if t.get("description"):
        print(f"\n{separator()}")
        print(f"  {bold('Beschreibung')}")
        for line in t["description"].splitlines():
            print(f"  {line}")

    comments = t.get("comments", [])
    if comments:
        print(f"\n{separator()}")
        print(f"  {bold('Kommentare')} ({len(comments)})")
        for c in comments:
            print(f"\n  {dim('▸')} {dim(c['time'])}")
            for line in c["text"].splitlines():
                print(f"    {line}")
    print(separator())

def cmd_update(args, data):
    """Ticket-Status oder Priorität ändern."""
    t = data["tickets"].get(str(args.id))
    if not t:
        print(red(f"✗ Ticket #{args.id} nicht gefunden."))
        return

    header(f"  TICKET #{t['id']} BEARBEITEN  ")
    print(f"  Aktuell: {fmt_status(t['status'])}  {fmt_priority(t['priority'])}\n")

    changed = False

    if args.status:
        if args.status not in STATUSES:
            print(red(f"✗ Ungültiger Status. Gültig: {', '.join(STATUSES)}"))
            return
        t["status"] = args.status
        changed = True
    elif not args.prioritaet:
        print(f"{bold('Neuer Status')} {dim('(Enter = unverändert)')}")
        s = choose("Auswahl", list(STATUSES.keys()), t["status"])
        if s != t["status"]:
            t["status"] = s
            changed = True

    if args.prioritaet:
        if args.prioritaet not in PRIORITIES:
            print(red(f"✗ Ungültige Priorität. Gültig: {', '.join(PRIORITIES)}"))
            return
        t["priority"] = args.prioritaet
        changed = True
    elif not args.status:
        print(f"\n{bold('Neue Priorität')} {dim('(Enter = unverändert)')}")
        p = choose("Auswahl", list(PRIORITIES.keys()), t["priority"])
        if p != t["priority"]:
            t["priority"] = p
            changed = True

    if changed:
        t["updated"] = now()
        save_data(data)
        print(f"\n{green('✓')} Ticket {ticket_id_str(t['id'])} aktualisiert.")
    else:
        print(dim("  Keine Änderungen."))

def cmd_kommentar(args, data):
    """Kommentar hinzufügen."""
    t = data["tickets"].get(str(args.id))
    if not t:
        print(red(f"✗ Ticket #{args.id} nicht gefunden."))
        return

    if args.text:
        text = args.text
    else:
        print(f"\n{bold('Kommentar')} für Ticket {ticket_id_str(args.id)}:")
        text = prompt("")

    if not text:
        print(yellow("ℹ Leerer Kommentar – abgebrochen."))
        return

    t.setdefault("comments", []).append({"time": now(), "text": text})
    t["updated"] = now()
    save_data(data)
    print(f"\n{green('✓')} Kommentar zu Ticket {ticket_id_str(args.id)} hinzugefügt.")

def cmd_loesche(args, data):
    """Ticket löschen."""
    tid = str(args.id)
    t = data["tickets"].get(tid)
    if not t:
        print(red(f"✗ Ticket #{args.id} nicht gefunden."))
        return
    
    print(f"\n{yellow('⚠')}  Ticket {ticket_id_str(tid)} wirklich löschen? {bold(t['title'])}")
    confirm = input("  Ja/Nein [N]: ").strip().lower()
    if confirm in ("ja", "j", "yes", "y"):
        del data["tickets"][tid]
        save_data(data)
        print(f"{green('✓')} Ticket #{tid} gelöscht.")
    else:
        print(dim("  Abgebrochen."))

def cmd_statistik(args, data):
    """Statistik anzeigen."""
    tickets = list(data["tickets"].values())
    if not tickets:
        print(yellow("ℹ Keine Tickets vorhanden."))
        return

    header("  STATISTIK  ")
    
    total = len(tickets)
    print(f"  {bold('Gesamt:')} {total} Tickets\n")
    
    print(f"  {bold('Nach Status:')}")
    for s in STATUSES:
        count = sum(1 for t in tickets if t["status"] == s)
        bar = "█" * count
        icon, color = STATUSES[s]
        print(f"    {color}{icon} {s:<12}{C.RESET} {bar} {dim(str(count))}")
    
    print(f"\n  {bold('Nach Priorität:')}")
    for p in PRIORITIES:
        count = sum(1 for t in tickets if t["priority"] == p)
        bar = "█" * count
        icon, color = PRIORITIES[p]
        print(f"    {color}{icon} {p:<10}{C.RESET} {bar} {dim(str(count))}")

    print(f"\n  {bold('Nach Kategorie:')}")
    for c in CATEGORIES:
        count = sum(1 for t in tickets if t["category"] == c)
        if count:
            print(f"    {fmt_category(c)} {dim(str(count))}")

# ─── Hauptprogramm ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="tickets",
        description=f"{bold('CLI Ticketsystem')}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dim(
            "Beispiele:\n"
            "  tickets neu\n"
            "  tickets liste --status offen\n"
            "  tickets liste --prioritaet hoch --sortierung prioritaet\n"
            "  tickets zeige 3\n"
            "  tickets update 3 --status gelöst\n"
            "  tickets kommentar 3 --text \"Problem reproduziert\"\n"
            "  tickets stats\n"
        )
    )
    sub = parser.add_subparsers(dest="cmd", metavar="BEFEHL")

    # neu
    sub.add_parser("neu", help="Neues Ticket erstellen")

    # liste
    p_list = sub.add_parser("liste", aliases=["ls"], help="Tickets auflisten")
    p_list.add_argument("--status", choices=list(STATUSES))
    p_list.add_argument("--prioritaet", choices=list(PRIORITIES))
    p_list.add_argument("--kategorie", choices=CATEGORIES)
    p_list.add_argument("--suche", metavar="TEXT")
    p_list.add_argument("--sortierung", choices=["id","datum","prioritaet","status"], default="id")

    # zeige
    p_show = sub.add_parser("zeige", aliases=["show"], help="Ticket-Details")
    p_show.add_argument("id", type=int, metavar="ID")

    # update
    p_upd = sub.add_parser("update", help="Status/Priorität ändern")
    p_upd.add_argument("id", type=int, metavar="ID")
    p_upd.add_argument("--status", choices=list(STATUSES))
    p_upd.add_argument("--prioritaet", choices=list(PRIORITIES))

    # kommentar
    p_cmt = sub.add_parser("kommentar", aliases=["cmt"], help="Kommentar hinzufügen")
    p_cmt.add_argument("id", type=int, metavar="ID")
    p_cmt.add_argument("--text", metavar="TEXT")

    # löschen
    p_del = sub.add_parser("loesche", aliases=["del", "rm"], help="Ticket löschen")
    p_del.add_argument("id", type=int, metavar="ID")

    # stats
    sub.add_parser("stats", help="Statistik anzeigen")

    args = parser.parse_args()
    data = load_data()

    dispatch = {
        "neu":      cmd_neu,
        "liste":    cmd_liste,
        "ls":       cmd_liste,
        "zeige":    cmd_zeige,
        "show":     cmd_zeige,
        "update":   cmd_update,
        "kommentar":cmd_kommentar,
        "cmt":      cmd_kommentar,
        "loesche":  cmd_loesche,
        "del":      cmd_loesche,
        "rm":       cmd_loesche,
        "stats":    cmd_statistik,
    }

    if args.cmd in dispatch:
        dispatch[args.cmd](args, data)
    else:
        # Interaktives Hauptmenü
        header("  CLI TICKETSYSTEM v1.0  ")
        tickets = data["tickets"]
        offen = sum(1 for t in tickets.values() if t["status"] == "offen")
        in_arbeit = sum(1 for t in tickets.values() if t["status"] == "in_arbeit")
        print(f"  {dim('Tickets:')} {yellow(str(offen))} offen  {blue(str(in_arbeit))} in Arbeit\n")
        print(f"  {bold('Befehle:')}")
        print(f"  {cyan('neu')}             Neues Ticket erstellen")
        print(f"  {cyan('liste')}           Alle Tickets anzeigen")
        print(f"  {cyan('zeige')} {dim('<id>')}      Ticket-Details")
        print(f"  {cyan('update')} {dim('<id>')}     Status/Priorität ändern")
        print(f"  {cyan('kommentar')} {dim('<id>')}  Kommentar hinzufügen")
        print(f"  {cyan('loesche')} {dim('<id>')}    Ticket löschen")
        print(f"  {cyan('stats')}           Statistik\n")
        print(dim(f"  Daten: {DATA_FILE}"))

if __name__ == "__main__":
    main()
