"""
stegaNSS Privacy Suite | Backend Interface Protocol
Author: Operative Suite Engine
Version: 2.4.0
License: Secure Intelligence Deployment
"""

import base64
import hashlib
import os
import sqlite3
import wave
from datetime import datetime

import cv2
import numpy as np
from flask import Flask, jsonify, redirect, render_template, request, send_file, session

# stegaNSS Core Utilities
import crypto_utils
import metadata_utils
from engines.audio_engine import AudioEngine
from engines.image_engine import StegaEngine
from engines.video_engine import VideoEngine

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
DB_PATH = os.environ.get("DATABASE_PATH", "database.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------------------------------------------------------
# DATABASE ARCHITECTURE
# -------------------------------------------------------------------------

def get_db():
    """Establishes an interface with the persistent intelligence database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the security database schema if not already present."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT, 
            password TEXT, 
            email TEXT UNIQUE, 
            bio TEXT, 
            specialization TEXT, 
            location TEXT, 
            department TEXT, 
            clearance TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT, 
            action_type TEXT, 
            media_type TEXT, 
            filename TEXT, 
            output_filename TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Forensic Handshake: Ensure output_filename exists in legacy databases
    try:
        cursor.execute("ALTER TABLE activity_log ADD COLUMN output_filename TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def log_activity(username, action, media, filename, output_filename=None):
    """Records security operations into the intelligence audit log."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activity_log (username, action_type, media_type, filename, output_filename) VALUES (?, ?, ?, ?, ?)", 
        (username, action, media, filename, output_filename)
    )
    conn.commit()
    conn.close()

# -------------------------------------------------------------------------
# AUTHENTICATION HUB
# -------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    """Standard operative authentication entry point."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db()
        result = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?", 
            (username, password)
        ).fetchone()
        conn.close()
        
        if result:
            session["user"] = username
            return redirect("/dashboard")
            
    return render_template("login.html")

@app.route("/google-login", methods=["POST"])
def google_login():
    """OAuth2 integration for secure Google identity verification."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
    
    token = request.form.get("credential")
    if not token: 
        return jsonify({"success": False, "error": "No credential provided"}), 400
        
    try:
        # Standard Client Validation
        CLIENT_ID = "183010381966-0nghig72cquqa21cclnpqg6btfbfid3j.apps.googleusercontent.com" 
        
        # Verify token with clock skew allowance for drift
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID, clock_skew=10)
        
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        conn = get_db()
        user_record = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        
        if not user_record:
            # Automatic operative registration
            conn.execute("INSERT INTO users(username, email) VALUES(?,?)", (name, email))
            conn.commit()
            user_record = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        
        conn.close()
        session["user"] = user_record["username"]
        return redirect("/dashboard")
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/register", methods=["GET", "POST"])
def register():
    """Manual registration interface for new operatives."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_db()
        conn.execute("INSERT INTO users(username, password) VALUES(?,?)", (username, password))
        conn.commit()
        conn.close()
        return redirect("/")
        
    return render_template("register.html")

# -------------------------------------------------------------------------
# DASHBOARD & PROFILE
# -------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    """Main command center displaying recent intelligence activity."""
    if "user" not in session: 
        return redirect("/")
        
    conn = get_db()
    logs = conn.execute(
        "SELECT * FROM activity_log WHERE username=? ORDER BY timestamp DESC LIMIT 5", 
        (session["user"],)
    ).fetchall()
    conn.close()
    
    return render_template("dashboard.html", logs=logs)

@app.route("/profile", methods=["GET", "POST"])
def profile():
    """Operative dossier management and history audit."""
    if "user" not in session: 
        return redirect("/")
        
    conn = get_db()
    if request.method == "POST":
        bio = request.form.get("bio")
        specialization = request.form.get("specialization")
        location = request.form.get("location")
        department = request.form.get("department")
        clearance = request.form.get("clearance")
        
        conn.execute(
            "UPDATE users SET bio=?, specialization=?, location=?, department=?, clearance=? WHERE username=?", 
            (bio, specialization, location, department, clearance, session["user"])
        )
        conn.commit()
        return redirect("/profile")
    
    user_data = conn.execute("SELECT * FROM users WHERE username=?", (session["user"],)).fetchone()
    logs = conn.execute(
        "SELECT * FROM activity_log WHERE username=? ORDER BY timestamp DESC", 
        (session["user"],)
    ).fetchall()
    conn.close()
    
    return render_template("profile.html", user=user_data, logs=logs)

@app.route("/delete_log/<int:log_id>")
def delete_log(log_id):
    """Forensic purge of a specific activity entry."""
    if "user" not in session: 
        return redirect("/")
        
    conn = get_db()
    log = conn.execute(
        "SELECT * FROM activity_log WHERE id=? AND username=?", 
        (log_id, session["user"])
    ).fetchone()
    
    if log:
        conn.execute("DELETE FROM activity_log WHERE id=?", (log_id,))
        conn.commit()
    conn.close()
    
    return redirect("/profile")
@app.route("/clear_history")
def clear_history():
    """Forensic purge of all activity entries for the active operative."""
    if "user" not in session: 
        return redirect("/")
        
    conn = get_db()
    conn.execute("DELETE FROM activity_log WHERE username=?", (session["user"],))
    conn.commit()
    conn.close()
    
    return redirect("/profile")

# -------------------------------------------------------------------------
# STEGANOGRAPHY PROTOCOLS
# -------------------------------------------------------------------------

@app.route("/select_hide")
def select_hide():
    """Gateway for payload integration based on media modality."""
    if "user" not in session: return redirect("/")
    return render_template("select_media.html", mode="hide")

@app.route("/select_extract")
def select_extract():
    """Gateway for payload recovery based on media modality."""
    if "user" not in session: return redirect("/")
    return render_template("select_media.html", mode="extract")

@app.route("/hide", methods=["GET", "POST"])
def hide():
    """Secures a payload into a carrier file using non-sequential LSB."""
    if "user" not in session: return redirect("/")
    
    media = request.args.get("media", "image")
    stego_file = None
    original_file = None
    
    if request.method == "POST":
        file = request.files["file"]
        original_file = file.filename
        secret, pin = request.form["secret"], request.form["pin"]
        media = request.form["media"]
        
        # Dual-Deception Layer Handling
        decoy_secret = request.form.get("decoy_secret")
        decoy_pin = request.form.get("decoy_pin")
        
        # 1. Primary Encryption
        primary_string = crypto_utils.encrypt_data(secret, pin)
        
        # 2. Optional Decoy Encryption
        decoy_string = None
        if decoy_secret and decoy_pin:
            decoy_string = crypto_utils.encrypt_data(decoy_secret, decoy_pin)
            
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        try:
            # Protocol Routing
            if media == "image":
                output_name = f"stega_{file.filename.split('.')[0]}.png"
                output_path = os.path.join(UPLOAD_FOLDER, output_name)
                StegaEngine.hide(path, primary_string, output_path, decoy_bytes=decoy_string)
                stego_file = output_name
            elif media == "audio":
                output_name = f"stega_{file.filename.split('.')[0]}.wav"
                output_path = os.path.join(UPLOAD_FOLDER, output_name)
                AudioEngine.hide(path, primary_string, output_path, decoy_bytes=decoy_string)
                stego_file = output_name
            elif media == "video":
                # Automated Intelligence Compression Protocol
                # Automatically downscale to 480p to optimize lossless footprint
                target_height = 480
                
                output_name = f"stega_{file.filename.split('.')[0]}_stego.mkv"
                output_path = os.path.join(UPLOAD_FOLDER, output_name)
                VideoEngine.hide(path, primary_string, output_path, decoy_bytes=decoy_string, target_height=target_height)
                stego_file = output_name
            
            log_activity(session["user"], "HIDE", media, file.filename, stego_file)
            # Re-confirm original_file for template consistency
            original_file = file.filename
        except Exception as e:
            return f"Cipher Deployment Failure: {str(e)}"

    return render_template("hide.html", stego_file=stego_file, original_file=original_file, media=media)

@app.route("/extract", methods=["GET", "POST"])
def extract():
    """Recovers encrypted payloads from artifacts via forensic scanning."""
    if "user" not in session: return redirect("/")
    
    media = request.args.get("media", "image")
    message = None
    success = False
    
    if request.method == "POST":
        file = request.files["file"]
        pin = request.form["pin"]
        media = request.form["media"]
        
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        
        try:
            # Layer Reconstruction
            if media == "image":
                even_layer, odd_layer = StegaEngine.extract(path)
            elif media == "audio":
                even_layer, odd_layer = AudioEngine.extract(path)
            elif media == "video":
                even_layer, odd_layer = VideoEngine.extract(path)
            else:
                return render_template("extract.html", msg="UNSUPPORTED MODALITY", media=media, success=False)

            if not even_layer and not odd_layer:
                message = "RECOVERY FAILED: No hidden stegaNSS signatures detected."
                success = False
            else:
                # Attempt Decryption (Standard Layer first, then Decoy)
                decrypted = crypto_utils.decrypt_data(even_layer, pin)
                if not decrypted: 
                    decrypted = crypto_utils.decrypt_data(odd_layer, pin)
                
                if decrypted:
                    message = decrypted
                    success = True
                    log_activity(session["user"], "EXTRACT", media, file.filename, file.filename)
                else: 
                    message = "ACCESS DENIED: Authentication PIN Failure."
                    success = False
        except Exception as e:
            message = f"Protocol Analysis Error: {e}"
            success = False

    return render_template("extract.html", msg=message, media=media, success=success)

# -------------------------------------------------------------------------
# ANALYTICS & VISUALIZATION API
# -------------------------------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Forensic metadata analysis targeting steganographic probability."""
    try:
        if "user" not in session: return jsonify({"success": False, "error": "Unauthorized"})
        file = request.files["file"]
        path = os.path.join(UPLOAD_FOLDER, "analyze_" + file.filename)
        file.save(path)
        
        score = 0
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            score = metadata_utils.analyze_stego_probability(path)
        
        if os.path.exists(path): os.remove(path)
        return jsonify({"success": True, "score": score})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/capacity", methods=["POST"])
def get_capacity():
    """Calculates payload volume boundaries for specific artifacts."""
    file = request.files["file"]
    media_type = request.form.get("media", "image")
    decoy_mode = request.form.get("decoy") == "true"
    
    temp_path = os.path.join(UPLOAD_FOLDER, "temp_" + file.filename)
    file.save(temp_path)
    
    # Calculate Carrier size on disk
    carrier_size = os.path.getsize(temp_path)
    carrier_size_human = f"{carrier_size} Bytes"
    if carrier_size > 1024 * 1024:
        carrier_size_human = f"{round(carrier_size / (1024 * 1024), 2)} MB"
    elif carrier_size > 1024:
        carrier_size_human = f"{round(carrier_size / 1024, 2)} KB"

    cap = 0
    if media_type == "image":
        cap = StegaEngine.get_max_capacity(temp_path, decoy_mode=decoy_mode)
    elif media_type == "audio":
        cap = AudioEngine.get_max_capacity(temp_path, decoy_mode=decoy_mode)
    elif media_type == "video":
        # Automated Intelligence Compression Protocol (480p Target)
        target_height = 480
        
        cap = VideoEngine.get_max_capacity(temp_path, decoy_mode=decoy_mode)
        v_cap = cv2.VideoCapture(temp_path)
        orig_h = v_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        v_cap.release()
        
        if orig_h > target_height:
            scale = target_height / orig_h
            cap = int(cap * (scale * scale))
        
    if os.path.exists(temp_path): os.remove(temp_path)
    
    # Payload capacity human conversion
    capacity_human = f"{cap} Bytes"
    if cap > 1024 * 1024:
        capacity_human = f"{round(cap / (1024 * 1024), 2)} MB"
    elif cap > 1024:
        capacity_human = f"{round(cap / 1024, 2)} KB"
        
    return jsonify({
        "success": True,
        "capacity": cap,
        "capacity_human": capacity_human,
        "carrier_size": carrier_size_human
    })

@app.route("/api/visualize", methods=["POST"])
def visualize():
    """Generates heatmaps highlighting steganographic mutations."""
    try:
        original_name = request.form.get("original")
        stego_name = request.form.get("stego")
        media_type = request.form.get("media")
        
        orig_path = os.path.join(UPLOAD_FOLDER, original_name)
        stego_path = os.path.join(UPLOAD_FOLDER, stego_name)
        
        if not os.path.exists(orig_path) or not os.path.exists(stego_path):
            return jsonify({"success": False, "error": "Source Files Missing"})

        if media_type == "image":
            orig = cv2.imread(orig_path)
            stego = cv2.imread(stego_path)
            
            if orig is None or stego is None:
                return jsonify({"success": False, "error": "Protocol IO Error."})

            if orig.shape != stego.shape:
                stego = cv2.resize(stego, (orig.shape[1], orig.shape[0]))

            # Multi-pass mutation detection
            diff = cv2.absdiff(orig, stego)
            mask_indices = np.any(diff > 0, axis=2)
            
            if not np.any(mask_indices):
                mask_indices = np.any((orig % 2) != (stego % 2), axis=2)

            # Total precision count at 100% resolution
            pixel_count = int(np.sum(mask_indices))
            
            # PERFORMANCE ACCELERATION: Downscale visualization if carrier is too large
            vis_w = 1000
            h, w, _ = orig.shape
            if w > vis_w:
                ratio = vis_w / float(w)
                new_size = (vis_w, int(h * ratio))
                orig_vis = cv2.resize(orig, new_size, interpolation=cv2.INTER_AREA)
                mask_vis = cv2.resize(mask_indices.astype(np.uint8), new_size, interpolation=cv2.INTER_NEAREST)
            else:
                orig_vis, mask_vis = orig, mask_indices.astype(np.uint8)

            # High-intensity Laser Scan visualization
            result = (orig_vis * 0.1).astype(np.uint8) # High-contrast dark background
            
            if np.any(mask_vis):
                binary_mask = mask_vis * 255
                kernel = np.ones((5,5), np.uint8) 
                dilated = cv2.dilate(binary_mask, kernel, iterations=1)
                glow = cv2.GaussianBlur(dilated, (9, 9), 0)
                
                # Applying Emerald Green masks for the "Laser Scan" bloom
                result[glow > 0] = [0, 80, 50]       # Ambient Aura
                result[dilated > 0] = [0, 255, 157] # Laser Core Data
            
            suspicion = metadata_utils.analyze_stego_probability(stego_path)
            # Use JPEG format with quality 85 for 4x faster transmission
            _, buffer = cv2.imencode(".jpg", result, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            encoded_img = base64.b64encode(buffer).decode("utf-8")
            
            return jsonify({
                "success": True, 
                "type": "image", 
                "data": encoded_img, 
                "score": suspicion,
                "note": f"Laser Scan identified {pixel_count} mutation vectors."
            })
            
        elif media_type == "video":
            cap_orig = cv2.VideoCapture(orig_path)
            cap_stego = cv2.VideoCapture(stego_path)
            
            # Target the middle frame for high-fidelity sampling
            total_frames = int(cap_stego.get(cv2.CAP_PROP_FRAME_COUNT))
            mid_frame = total_frames // 2
            cap_stego.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            cap_orig.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            
            ret1, stego_f = cap_stego.read()
            ret2, orig_f = cap_orig.read()
            
            if not ret1 or stego_f is None:
                stego_f = np.zeros((480, 854, 3), dtype=np.uint8)
                orig_f = np.zeros_like(stego_f)
            
            if stego_f.shape != orig_f.shape:
                orig_f = cv2.resize(orig_f, (stego_f.shape[1], stego_f.shape[0]))

            # CLONE LOGIC: EXACT MATCH TO IMAGE ENGINE
            diff = cv2.absdiff(orig_f, stego_f)
            mask_indices = np.any(diff > 0, axis=2)
            pixel_count = int(np.sum(mask_indices))
            
            # Targeted Resolution Scaling
            vis_w = 1000
            h, w, _ = stego_f.shape
            if w > vis_w:
                ratio = vis_w / float(w)
                new_sz = (vis_w, int(h * ratio))
                stego_vis = cv2.resize(stego_f, new_sz, interpolation=cv2.INTER_AREA)
                mask_vis = cv2.resize(mask_indices.astype(np.uint8), new_sz, interpolation=cv2.INTER_NEAREST)
            else:
                stego_vis, mask_vis = stego_f, mask_indices.astype(np.uint8)

            # High-intensity Laser Scan visualization (Identical to Image)
            result = (stego_vis * 0.1).astype(np.uint8) 
            
            if np.any(mask_vis):
                binary_mask = mask_vis * 255
                kernel = np.ones((5,5), np.uint8)
                dilated = cv2.dilate(binary_mask, kernel, iterations=1)
                glow = cv2.GaussianBlur(dilated, (9, 9), 0)
                
                result[glow > 0] = [0, 80, 50]       # Ambient Aura
                result[dilated > 0] = [0, 255, 157] # Laser Core Data
            
            cap_orig.release()
            cap_stego.release()

            # High-Speed JPEG Encoding
            _, buffer = cv2.imencode(".jpg", result, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            encoded_img = base64.b64encode(buffer).decode("utf-8")
            
            return jsonify({
                "success": True, 
                "type": "image", 
                "data": encoded_img, 
                "note": f"Laser Scan identified {pixel_count} mutation vectors."
            })

        elif media_type == "audio":
            import wave
            with wave.open(stego_path, 'rb') as wav:
                frames_stego = wav.readframes(wav.getnframes())
                audio_bytes_stego = np.frombuffer(frames_stego, dtype=np.uint8)
            with wave.open(orig_path, 'rb') as wav_orig:
                frames_orig = wav_orig.readframes(wav_orig.getnframes())
                audio_bytes_orig = np.frombuffer(frames_orig, dtype=np.uint8)
                
            min_len = min(len(audio_bytes_stego), len(audio_bytes_orig))
            chunk_size = max(1, min_len // 1000)
            impact = []
            total_mutations = 0
            
            energy = []
            for i in range(0, 1000):
                start = i * chunk_size
                end = min(start + chunk_size, min_len)
                if start >= min_len:
                    impact.append(0); energy.append(0); continue
                
                # Spectral Resonance Analysis (FFT)
                chunk_o = audio_bytes_orig[start:end]
                signal = (chunk_o.astype(np.float32) - 128) / 128.0
                if len(signal) > 10:
                    fft_res = np.abs(np.fft.rfft(signal))
                    energy.append(np.mean(fft_res))
                else: energy.append(0)

                impact.append(np.sum(audio_bytes_stego[start:end] != chunk_o))
                total_mutations += impact[-1]
            
            # DUAL-PANE FORENSIC DASHBOARD (V2.2 Clear-View)
            h, w = 350, 1000
            vis = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.line(vis, (0, h//2 + 20), (w, h//2 + 20), (30,30,30), 1) # Splitter
            
            detected_bytes = total_mutations // 8
            # 1. Carrier Signal Envelope (Top Pane)
            max_eng = max(energy) if max(energy) > 0 else 1
            for x, eng in enumerate(energy):
                if x >= w: break
                eng_h = int((eng / max_eng) * 120)
                cv2.line(vis, (x, 100 + eng_h), (x, 100 - eng_h), (40, 20, 10), 1)
            cv2.putText(vis, "SIGNAL ENVELOPE (CARRIER)", (15, 25), 0, 0.45, (80,80,80), 1)

            # 2. Payload Density Map (Bottom Pane)
            max_imp = max(impact) if max(impact) > 0 else 1
            for x, val in enumerate(impact):
                if x >= w: break
                if val > 0:
                    density_h = int((val / max_imp) * 140)
                    cv2.rectangle(vis, (x, h - 25), (x + 1, h - 25 - density_h), (0, 255, 157), -1)
            
            cv2.putText(vis, f"PAYLOAD DENSITY: {detected_bytes} BYTES", (15, h//2 + 50), 0, 0.6, (0, 255, 157), 2)
            cv2.putText(vis, "EMERALD BLOCKS INDICATE MUTATED BIT-ZONE DENSITY", (15, h - 10), 0, 0.4, (100,100,100), 1)
            
            # Mission Footer
            cv2.putText(vis, "stegaNSS FORENSIC SUITE v3.0", (780, 25), 0, 0.35, (50,50,50), 1)
            
            _, buffer = cv2.imencode(".png", vis)
            encoded_img = base64.b64encode(buffer).decode("utf-8")
            return jsonify({
                "success": True, "type": "audio", "data": encoded_img, 
                "note": f"Spectral Scan: {detected_bytes} Bytes mapped to the frequency spectrum. Emerald spikes indicate resonance-locked payload vectors."
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# -------------------------------------------------------------------------
# SYSTEM UTILITIES
# -------------------------------------------------------------------------

@app.route("/download/<filename>")
def download(filename):
    """Secure artifact transmission protocol."""
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)



@app.route("/logout")
def logout():
    """Terminates the active operative session."""
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)