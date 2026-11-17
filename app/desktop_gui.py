"""Native desktop control panel for PRNTR Treasure Tracker."""
import os
import subprocess
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

BG="#081018"; PANEL="#152935"; GOLD="#ffc975"; MINT="#72edd0"; WHITE="#f4fbfb"; MUTED="#91acb8"
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
    root.geometry("1200x840")
    root.minsize(1000,760)
    root.configure(bg=BG)
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    def label(parent,text,size=11,fg=WHITE,bold=False):
        return tk.Label(parent,text=text,bg=parent.cget("bg"),fg=fg,font=("Segoe UI",size,"bold" if bold else "normal"))
    def panel(parent):
        return tk.Frame(parent,bg=PANEL,padx=19,pady=18,highlightbackground="#304e5d",highlightthickness=1)
    def button(parent,text,fn,accent=False):
        return tk.Button(parent,text=text,command=fn,fg=BG if accent else WHITE,bg=GOLD if accent else "#223c49",
            activebackground="#ffdf9b" if accent else "#45626d",bd=0,padx=12,pady=9,font=("Segoe UI",10,"bold"),cursor="hand2")
    def act(name,val=None):
        try:
            update(name,val)
        except (ValueError,TypeError) as error:
            messagebox.showerror("Treasure Tracker",str(error),parent=root)
    outer=tk.Frame(root,bg=BG,padx=22,pady=22)
    outer.pack(fill="both",expand=True)
    outer.grid_rowconfigure(0,weight=1)
    outer.grid_columnconfigure(1,weight=1)
    side=tk.Frame(outer,bg="#0d1821",width=265,padx=18,pady=22,
                  highlightbackground="#304e5d",highlightthickness=1)
    side.grid(row=0,column=0,sticky="nsw",padx=(0,18))
    side.grid_propagate(False)
    label(side,"PRNTR / STREAM TOOLS",10,MINT,True).pack(anchor="w")
    label(side,"TREASURE\\nTRACKER",27,GOLD,True).pack(anchor="w",pady=(8,7))
    label(side,"LOCAL PROFILES  /  PIRATE EDITION",9,MINT,True).pack(anchor="w")
    tk.Label(side,text="Stream-ready chest tracking with hotkeys, team presets and a dedicated overlay.",
             bg=side.cget("bg"),fg=MUTED,font=("Segoe UI",10),wraplength=214,justify="left").pack(anchor="w",pady=(12,20))
    status=tk.Frame(side,bg="#122630",padx=15,pady=14)
    status.pack(fill="x",pady=(0,14))
    label(status,"● LIVE STATUS",10,MINT,True).pack(anchor="w")
    label(status,"Ready to count chests",12,WHITE,True).pack(anchor="w",pady=(7,0))
    profile_box=panel(side);profile_box.pack(fill="x",pady=(0,14))
    label(profile_box,"YOUR TRACKER",11,WHITE,True).pack(anchor="w",pady=(0,6))
    label(profile_box,"Choose a profile or create a new one.",9,MUTED).pack(anchor="w",pady=(0,8))
    profile_name=tk.StringVar(value="default")
    profile_choices=ttk.Combobox(profile_box,textvariable=profile_name,state="readonly")
    profile_choices.pack(fill="x",pady=(0,9))
    profile_new=tk.StringVar()
    name_entry=tk.Entry(profile_box,textvariable=profile_new,bg=BG,fg=WHITE,
                        insertbackground=GOLD,highlightbackground="#39545d",highlightthickness=1,
                        bd=0,font=("Segoe UI",11))
    name_entry.pack(fill="x",ipady=7,pady=(0,8))
    label(profile_box,"New username (letters, numbers, _ or -)",8,MUTED).pack(anchor="w",pady=(0,7))
    def switch_profile():
        act("profile_select",profile_name.get())
    def create_profile():
        username=profile_new.get().strip()
        if username:
            try:
                update("profile_create",username)
                profile_new.set("")
            except (ValueError,TypeError) as error:
                messagebox.showerror("Treasure Tracker",str(error),parent=root)
    button(profile_box,"Switch tracker",switch_profile).pack(fill="x",pady=(0,6))
    button(profile_box,"Create my tracker",create_profile,True).pack(fill="x")
    profile_choices.bind("<<ComboboxSelected>>",lambda event: switch_profile())
    quick=panel(side);quick.pack(fill="x",pady=(0,14))
    label(quick,"QUICK ACTIONS",11,WHITE,True).pack(anchor="w",pady=(0,10))
    button(quick,"+ ADD CHEST",lambda:act("open"),True).pack(fill="x",pady=(0,8))
    button(quick,"Undo last click",lambda:act("undo")).pack(fill="x",pady=(0,8))
    button(quick,"Open overlay",lambda:open_overlay(data_dir)).pack(fill="x")
    presets=panel(side);presets.pack(fill="x")
    label(presets,"TEAM PRESETS",11,WHITE,True).pack(anchor="w",pady=(0,9))
    label(presets,"Change chests per click instantly.",9,MUTED).pack(anchor="w",pady=(0,9))
    for name,amount in (("SOLO",1),("DUO",2),("TRIO",3),("SQUAD",4)):
        button(presets,name+"  •  "+str(amount),lambda n=amount:act("chests_per_click",n)).pack(fill="x",pady=(0,5))
    body=tk.Frame(outer,bg=BG)
    body.grid(row=0,column=1,sticky="nsew")
    header=panel(body)
    header.pack(fill="x",pady=(0,15))
    label(header,"PIRATE EDITION  /  DESKTOP",10,MINT,True).pack(anchor="w")
    label(header,"Track every chest like it matters.",23,WHITE,True).pack(anchor="w",pady=(5,4))
    label(header,"Instant counting • Squad presets • Live TikTok / OBS overlay",10,MUTED).pack(anchor="w")
    statistics=tk.Frame(body,bg=BG); statistics.pack(fill="x")
    counts={}
    for i,(key,name) in enumerate((("chests","CHESTS OPENED"),("tokens","TREASURE FOUND"),("rate","CHESTS / HOUR"))):
        c=panel(statistics);c.grid(row=0,column=i,sticky="nsew",padx=(0,8) if i<2 else 0)
        statistics.grid_columnconfigure(i,weight=1)
        label(c,name,9,MUTED,True).pack(anchor="w")
        counts[key]=tk.StringVar(value="0")
        tk.Label(c,textvariable=counts[key],font=("Segoe UI",31,"bold"),bg=PANEL,fg=GOLD if i==0 else MINT if i==1 else WHITE).pack(anchor="w")
    actions=panel(body);actions.pack(fill="x",pady=(12,0))
    label(actions,"CHEST CONTROLS",13,WHITE,True).pack(anchor="w",pady=(0,8))
    label(actions,"Use your game hotkey or the button below.",9,MUTED).pack(anchor="w",pady=(0,10))
    controls=tk.Frame(actions,bg=PANEL);controls.pack(fill="x")
    button(controls,"+ CHEST OPENED",lambda:act("open"),True).pack(side="left",fill="x",expand=True,padx=(0,7))
    button(controls,"Undo last click",lambda:act("undo")).pack(side="left")
    settings=panel(body);settings.pack(fill="x",pady=(12,0))
    label(settings,"SETTINGS  /  PERSONALISE YOUR COUNTING",13,WHITE,True).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,7))
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
    label(streaming,"STREAM OVERLAY  /  TIKTOK + OBS",13,WHITE,True).pack(anchor="w")
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
        choices=s.get("profiles",["default"])
        if tuple(profile_choices["values"])!=tuple(choices):
            profile_choices["values"]=choices
        if root.focus_get() not in (profile_choices,name_entry):
            profile_name.set(s.get("username","default"))
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
