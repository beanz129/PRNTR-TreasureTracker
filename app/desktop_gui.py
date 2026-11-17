"""Native desktop control panel for PRNTR Treasure Tracker."""
import os
import subprocess
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

BG="#0b141c"; PANEL="#15252e"; GOLD="#ffcf80"; MINT="#81e9ca"; WHITE="#f0f5f5"; MUTED="#9bb2b7"
URL="http://127.0.0.1:8765/overlay"

def open_overlay(data_dir):
    roots=[os.environ.get("PROGRAMFILES(X86)",r"C:\Program Files (x86)"),os.environ.get("PROGRAMFILES",r"C:\Program Files")]
    browser_paths=[Path(r)/s for r in roots for s in ("Microsoft/Edge/Application/msedge.exe","Google/Chrome/Application/chrome.exe")]
    for browser in browser_paths:
        if browser.is_file():
            try:
                subprocess.Popen([str(browser),"--user-data-dir="+str(data_dir/"browser-profile"),
                    "--app="+URL,"--window-size=680,230","--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding","--disable-backgrounding-occluded-windows",
                    "--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling,TabFreeze"],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                return
            except OSError:
                pass
    webbrowser.open(URL)

def launch(snapshot, update, data_dir, shutdown):
    root=tk.Tk()
    root.title("PRNTR • Treasure Tracker")
    root.geometry("820x735")
    root.minsize(690,670)
    root.configure(bg=BG)
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    def label(parent,text,size=11,fg=WHITE,bold=False):
        return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=fg,font=("Segoe UI",size,"bold" if bold else "normal"))
    def panel(parent):
        return tk.Frame(parent,bg=PANEL,padx=17,pady=15,highlightbackground="#39545d",highlightthickness=1)
    def button(parent,text,fn,accent=False):
        return tk.Button(parent,text=text,command=fn,fg=BG if accent else WHITE,bg=GOLD if accent else "#304852",
            activebackground="#ffe0a0" if accent else "#45626d",bd=0,padx=12,pady=9,font=("Segoe UI",10,"bold"),cursor="hand2")
    def act(name,val=None):
        try:
            update(name,val)
        except (ValueError,TypeError) as error:
            messagebox.showerror("Treasure Tracker",str(error),parent=root)
    body=tk.Frame(root,bg=BG,padx=20,pady=17)
    body.pack(fill="both",expand=True)
    label(body,"PRNTR / STREAM TOOLS",10,MINT,True).pack(anchor="w")
    label(body,"TREASURE TRACKER",26,GOLD,True).pack(anchor="w",pady=(3,0))
    label(body,"Standalone Windows controls • Live TikTok/OBS overlay",10,MUTED).pack(anchor="w",pady=(0,13))
    statistics=tk.Frame(body,bg=BG); statistics.pack(fill="x")
    counts={}
    for i,(key,name) in enumerate((("chests","CHESTS OPENED"),("tokens","TREASURE FOUND"),("rate","CHESTS / HOUR"))):
        c=panel(statistics);c.grid(row=0,column=i,sticky="nsew",padx=(0,8) if i<2 else 0)
        statistics.grid_columnconfigure(i,weight=1)
        label(c,name,9,MUTED,True).pack(anchor="w")
        counts[key]=tk.StringVar(value="0")
        tk.Label(c,textvariable=counts[key],font=("Segoe UI",26,"bold"),bg=PANEL,fg=GOLD if i==0 else MINT if i==1 else WHITE).pack(anchor="w")
    actions=panel(body);actions.pack(fill="x",pady=(12,0))
    label(actions,"CHEST CONTROLS",12,WHITE,True).pack(anchor="w",pady=(0,8))
    controls=tk.Frame(actions,bg=PANEL);controls.pack(fill="x")
    button(controls,"+ CHEST OPENED",lambda:act("open"),True).pack(side="left",fill="x",expand=True,padx=(0,7))
    button(controls,"Undo last click",lambda:act("undo")).pack(side="left")
    settings=panel(body);settings.pack(fill="x",pady=(12,0))
    label(settings,"SETTINGS",12,WHITE,True).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,7))
    settings.grid_columnconfigure(1,weight=1)
    def setting_label(text,row):
        label(settings,text,10,MUTED,True).grid(row=row,column=0,sticky="w",padx=(0,10),pady=6)
    key=tk.StringVar();enabled=tk.BooleanVar();chests=tk.StringVar();treasure=tk.StringVar()
    setting_label("Global hotkey",1)
    style=ttk.Style(root);style.theme_use("clam")
    style.configure("Tracker.TCombobox",fieldbackground=BG,background=PANEL,foreground=WHITE,padding=7)
    combo=ttk.Combobox(settings,textvariable=key,values=("MIDDLE MOUSE","MOUSE 4 (SIDE)","MOUSE 5 (SIDE)","F6","F7","F8","F9","F10","F11","F12","NUMPAD +"),state="readonly",style="Tracker.TCombobox")
    combo.grid(row=1,column=1,sticky="ew")
    combo.bind("<<ComboboxSelected>>",lambda event:act("hotkey",key.get()))
    fields=[]
    for row,text,var,action in ((2,"Chests per click (squads)",chests,"chests_per_click"),(3,"Treasure per chest (0 allowed)",treasure,"per_chest")):
        setting_label(text,row)
        cell=tk.Frame(settings,bg=PANEL);cell.grid(row=row,column=1,sticky="ew",pady=4)
        entry=tk.Entry(cell,textvariable=var,bg=BG,fg=WHITE,insertbackground=GOLD,bd=0,highlightthickness=1,highlightbackground="#39545d",font=("Segoe UI",11))
        entry.pack(side="left",fill="x",expand=True,ipady=8,padx=(0,8))
        button(cell,"Save",lambda a=action,v=var:act(a,v.get())).pack(side="left")
        entry.bind("<Return>",lambda e,a=action,v=var:act(a,v.get()))
        fields.append((entry,var,"chests_per_click" if action=="chests_per_click" else "tokens_per_chest"))
    tk.Checkbutton(settings,text="Global hotkey enabled",variable=enabled,command=lambda:act("enabled",enabled.get()),
        bg=PANEL,fg=WHITE,activebackground=PANEL,activeforeground=WHITE,selectcolor=BG).grid(row=4,column=0,columnspan=2,sticky="w",pady=(7,0))
    streaming=panel(body);streaming.pack(fill="x",pady=(12,0))
    label(streaming,"STREAM OVERLAY",12,WHITE,True).pack(anchor="w")
    label(streaming,"Window Capture: capture the separate overlay window and leave it unminimised.",9,MUTED).pack(anchor="w",pady=(3,8))
    overlay_actions=tk.Frame(streaming,bg=PANEL);overlay_actions.pack(fill="x")
    button(overlay_actions,"Open overlay",lambda:open_overlay(data_dir),True).pack(side="left",padx=(0,8))
    def copy_url():
        root.clipboard_clear();root.clipboard_append(URL)
    button(overlay_actions,"Copy local URL",copy_url).pack(side="left",padx=(0,8))
    button(overlay_actions,"Reset session",lambda:act("reset") if messagebox.askyesno("Reset session","Reset both totals to zero?",parent=root) else None).pack(side="right")
    def refresh():
        if not root.winfo_exists():
            return
        s=snapshot()
        counts["chests"].set(f'{s["chests"]:,}')
        counts["tokens"].set(f'{s["tokens"]:,}')
        counts["rate"].set(f'{int(s["chests"]*3600/max(1,time.time()-s["session_started"])):,}')
        if root.focus_get()!=combo: key.set(s["hotkey"])
        enabled.set(s["enabled"])
        for entry,var,state_key in fields:
            if root.focus_get() != entry: var.set(str(s[state_key]))
        root.after(250,refresh)
    def close():
        root.destroy()
    root.protocol("WM_DELETE_WINDOW",close)
    try:
        refresh(); root.after(600,lambda:open_overlay(data_dir));root.mainloop()
    finally:
        shutdown()
