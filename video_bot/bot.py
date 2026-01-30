import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    ContextTypes, 
    MessageHandler, 
    filters,
    CallbackQueryHandler
)

# ===================== CONFIGURATION =====================
BOT_TOKEN = "8006015641:AAHMiqhkmtvRmdLMN1Rbz2EnwsIrsGfH8qU"  # আপনার Video Delivery Bot Token
CHANNEL_ID = -1003872857468  # ভিডিও চ্যানেল ID
CHANNEL_USERNAME = "@Cinaflixsteem"  # ভিডিও চ্যানেল username
ADMIN_ID = 1858324638  # আপনার Telegram User ID
DATABASE_FILE = "channels.json"

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== DATABASE FUNCTIONS =====================
def load_database():
    """Load database from JSON file"""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create default database
        default_db = {
            "force_join_channels": [
                {
                    "id": CHANNEL_ID,
                    "username": CHANNEL_USERNAME,
                    "name": "CINEFLIX Main Channel"
                }
            ],
            "promo_channels": [],
            "admin_id": ADMIN_ID,
            "stats": {
                "total_users": [],
                "videos_sent_today": 0,
                "total_videos_sent": 0
            }
        }
        save_database(default_db)
        return default_db

def save_database(db):
    """Save database to JSON file"""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# ===================== GLOBAL DATABASE =====================
db = load_database()

# ===================== START COMMAND =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - supports deep linking for video playback"""
    user = update.effective_user
    
    # Add user to database
    if user.id not in db['stats']['total_users']:
        db['stats']['total_users'].append(user.id)
        save_database(db)
    
    # Check if this is a video request (deep link)
    if context.args and len(context.args) > 0:
        video_id = context.args[0]
        await handle_video_request(update, context, video_id)
        return
    
    # Normal start - show welcome message
    keyboard = [
        [InlineKeyboardButton("🎬 Open CINEFLIX App", url="https://cinaflix-streaming.vercel.app/")],
        [InlineKeyboardButton("📢 Join Main Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎬 **Welcome to CINEFLIX Video Bot!**

Hello **{user.first_name}**! 👋

এই বট আপনাকে **Premium Quality Videos** দিবে!

**🚀 কিভাবে ব্যবহার করবেন:**
1️⃣ CINEFLIX App open করুন
2️⃣ যেকোনো video select করুন
3️⃣ "Watch Now" ক্লিক করুন
4️⃣ ভিডিও পেয়ে যাবেন! 🍿

**📢 গুরুত্বপূর্ণ:**
- ভিডিও পেতে আমাদের channel join করুন
- Premium HD quality videos
- Regular updates

Happy Watching! 🎉
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ===================== VIDEO REQUEST HANDLER =====================
async def handle_video_request(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str):
    """Handle video playback request from Mini App"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"🎬 Video request from {user.id} (@{user.username}) for video: {video_id}")
    
    try:
        # Check all force join channels
        not_joined_channels = []
        
        for channel in db['force_join_channels']:
            try:
                member = await context.bot.get_chat_member(channel['id'], user.id)
                is_member = member.status in ['member', 'administrator', 'creator']
                if not is_member:
                    not_joined_channels.append(channel)
            except Exception as e:
                logger.error(f"❌ Error checking membership for {channel['username']}: {e}")
                not_joined_channels.append(channel)
        
        # If user hasn't joined all channels
        if not_joined_channels:
            await show_force_join_message(update, context, not_joined_channels, video_id)
            return
        
        # User has joined all channels - send video
        await send_video(update, context, video_id, chat_id)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_video_request: {e}")
        await update.message.reply_text(
            "❌ **কিছু ভুল হয়েছে!**\n\n"
            "আবার চেষ্টা করুন অথবা admin এর সাথে যোগাযোগ করুন।",
            parse_mode='Markdown'
        )

async def show_force_join_message(update: Update, context: ContextTypes.DEFAULT_TYPE, channels, video_id):
    """Show force join message with all channels"""
    keyboard = []
    
    # Add join buttons for each channel
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(
                f"📢 Join {channel['name']}", 
                url=f"https://t.me/{channel['username'].replace('@', '')}"
            )
        ])
    
    # Add retry button
    keyboard.append([
        InlineKeyboardButton(
            "✅ আমি সব চ্যানেল জয়েন করেছি - আবার চেষ্টা করুন", 
            callback_data=f"verify_{video_id}"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    channel_list = "\n".join([f"• {ch['name']}" for ch in channels])
    
    message_text = f"""
🔒 **Content Locked!**

ভিডিও দেখার জন্য নিচের **সব চ্যানেল** জয়েন করুন:

{channel_list}

**📝 Steps:**
1️⃣ নিচে সব "Join" বাটনে ক্লিক করুন
2️⃣ প্রতিটি চ্যানেল জয়েন করুন
3️⃣ "আমি সব চ্যানেল জয়েন করেছি" বাটনে ক্লিক করুন

জয়েন করার পর instant access পাবেন! 🎉
    """
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str, chat_id: int):
    """Send video to user after verification"""
    try:
        # Forward message from channel
        await context.bot.forward_message(
            chat_id=chat_id,
            from_chat_id=CHANNEL_ID,
            message_id=int(video_id)
        )
        
        # Update stats
        db['stats']['videos_sent_today'] += 1
        db['stats']['total_videos_sent'] += 1
        save_database(db)
        
        # Send success message with promo
        keyboard = [
            [InlineKeyboardButton("🎬 আরো ভিডিও দেখুন", url="https://cinaflix-streaming.vercel.app/")],
            [InlineKeyboardButton("📢 CINEFLIX Main Bot", url="https://t.me/YOUR_MAIN_BOT_USERNAME")]
        ]
        
        await update.message.reply_text(
            "✅ **Enjoy Watching!**\n\n"
            "🎬 আরো Premium Content দেখতে CINEFLIX App browse করুন!\n"
            "📢 Latest updates এর জন্য আমাদের Main Bot follow করুন!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Successfully sent video {video_id} to user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"❌ Error forwarding video {video_id}: {e}")
        await update.message.reply_text(
            "❌ **Video Not Found!**\n\n"
            "এই ভিডিওটি মুছে ফেলা হয়েছে অথবা link সঠিক নয়।\n"
            "App থেকে অন্য ভিডিও দেখুন।",
            parse_mode='Markdown'
        )

# ===================== CALLBACK QUERY HANDLER =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        help_text = """
🎬 **CINEFLIX Video Bot Help**

**কিভাবে ব্যবহার করবেন:**
1. CINEFLIX App open করুন
2. ভিডিও select করুন
3. "Watch Now" ক্লিক করুন
4. সব চ্যানেল জয়েন করুন
5. ভিডিও পাবেন!

**সমস্যা হলে:**
❓ ভিডিও আসছে না? সব চ্যানেল জয়েন করেছেন কিনা check করুন
❓ App load হচ্ছে না? Internet connection check করুন

**Support:**
Admin এর সাথে যোগাযোগ করুন

Enjoy! 🍿
        """
        await query.message.reply_text(help_text, parse_mode='Markdown')
    
    elif data.startswith("verify_"):
        # User claims they joined - verify again
        video_id = data.replace("verify_", "")
        
        # Create fake update for handler
        update.message = query.message
        await handle_video_request(update, context, video_id)
    
    elif data.startswith("admin_"):
        # Admin panel callbacks
        await handle_admin_callback(update, context, data)

# ===================== ADMIN PANEL =====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ এই command শুধুমাত্র admin এর জন্য!")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("➕ চ্যানেল Add করুন", callback_data="admin_add_channel"),
            InlineKeyboardButton("➖ চ্যানেল Remove করুন", callback_data="admin_remove_channel")
        ],
        [
            InlineKeyboardButton("📋 সব চ্যানেল দেখুন", callback_data="admin_list_channels"),
            InlineKeyboardButton("📊 Statistics দেখুন", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("📢 Broadcast করুন", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔄 Database Backup", callback_data="admin_backup")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    panel_text = f"""
🎛️ **CINEFLIX Admin Panel**

Welcome, Admin! 👑

**Quick Stats:**
👥 Total Users: **{len(db['stats']['total_users'])}**
📹 Videos Sent Today: **{db['stats']['videos_sent_today']}**
📊 Total Videos Sent: **{db['stats']['total_videos_sent']}**

**Force Join Channels:** {len(db['force_join_channels'])}

আপনি কি করতে চান?
    """
    
    await update.message.reply_text(
        panel_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Handle admin panel callbacks"""
    query = update.callback_query
    
    if data == "admin_list_channels":
        channels_text = "📋 **Force Join Channels:**\n\n"
        
        for i, ch in enumerate(db['force_join_channels'], 1):
            channels_text += f"{i}. **{ch['name']}**\n"
            channels_text += f"   ID: `{ch['id']}`\n"
            channels_text += f"   Username: {ch['username']}\n\n"
        
        if not db['force_join_channels']:
            channels_text += "_কোনো চ্যানেল নেই_"
        
        await query.message.reply_text(channels_text, parse_mode='Markdown')
    
    elif data == "admin_stats":
        stats_text = f"""
📊 **Detailed Statistics**

**Users:**
👥 Total Users: {len(db['stats']['total_users'])}

**Videos:**
📹 Sent Today: {db['stats']['videos_sent_today']}
📊 Total Sent: {db['stats']['total_videos_sent']}

**Channels:**
📢 Force Join Channels: {len(db['force_join_channels'])}
🎯 Promo Channels: {len(db['promo_channels'])}

**Bot Status:** ✅ Running

Last Updated: {context.application.bot.name}
        """
        await query.message.reply_text(stats_text, parse_mode='Markdown')
    
    elif data == "admin_add_channel":
        instruction = """
➕ **চ্যানেল Add করুন**

নিচের format এ message পাঠান:

`/addchannel CHANNEL_ID @username Channel Name`

**উদাহরণ:**
`/addchannel -1001234567890 @MyChannel My Channel Name`

**Note:**
- Channel ID পেতে bot কে channel এ admin বানান
- তারপর `/getid` command দিন channel এ
        """
        await query.message.reply_text(instruction, parse_mode='Markdown')
    
    elif data == "admin_remove_channel":
        if not db['force_join_channels']:
            await query.message.reply_text("❌ কোনো চ্যানেল নেই remove করার জন্য!")
            return
        
        keyboard = []
        for ch in db['force_join_channels']:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Remove {ch['name']}", 
                    callback_data=f"remove_ch_{ch['id']}"
                )
            ])
        
        await query.message.reply_text(
            "❌ **কোন চ্যানেল remove করবেন?**",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("remove_ch_"):
        ch_id = int(data.replace("remove_ch_", ""))
        
        # Find and remove channel
        removed = None
        for ch in db['force_join_channels']:
            if ch['id'] == ch_id:
                removed = ch
                db['force_join_channels'].remove(ch)
                break
        
        if removed:
            save_database(db)
            await query.message.reply_text(
                f"✅ **চ্যানেল সফলভাবে remove করা হয়েছে!**\n\n"
                f"**Removed:** {removed['name']}",
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text("❌ চ্যানেল পাওয়া যায়নি!")
    
    elif data == "admin_backup":
        # Send database file
        with open(DATABASE_FILE, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename="cineflix_backup.json",
                caption="💾 **Database Backup**\n\nCurrent database backup"
            )
    
    elif data == "admin_broadcast":
        instruction = """
📢 **Broadcast Message**

সব users কে message পাঠাতে:

`/broadcast আপনার message এখানে লিখুন`

**উদাহরণ:**
`/broadcast নতুন সিরিজ আপডেট! এখনই দেখুন 🎬`
        """
        await query.message.reply_text(instruction, parse_mode='Markdown')

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new force join channel (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ **ভুল format!**\n\n"
            "সঠিক format:\n"
            "`/addchannel -1001234567890 @username Channel Name`",
            parse_mode='Markdown'
        )
        return
    
    try:
        channel_id = int(context.args[0])
        username = context.args[1]
        name = ' '.join(context.args[2:])
        
        # Check if already exists
        for ch in db['force_join_channels']:
            if ch['id'] == channel_id:
                await update.message.reply_text("⚠️ এই চ্যানেল already যুক্ত আছে!")
                return
        
        # Add to database
        db['force_join_channels'].append({
            "id": channel_id,
            "username": username,
            "name": name
        })
        save_database(db)
        
        await update.message.reply_text(
            f"✅ **চ্যানেল সফলভাবে যুক্ত করা হয়েছে!**\n\n"
            f"**Name:** {name}\n"
            f"**Username:** {username}\n"
            f"**ID:** `{channel_id}`\n\n"
            f"এখন থেকে users কে এই চ্যানেল join করতে হবে!",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Added new channel: {name} ({username})")
        
    except ValueError:
        await update.message.reply_text("❌ Channel ID একটি number হতে হবে!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users (Admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Usage:**\n\n"
            "`/broadcast Your message here`",
            parse_mode='Markdown'
        )
        return
    
    message = ' '.join(context.args)
    success = 0
    failed = 0
    
    status_msg = await update.message.reply_text("📤 Broadcasting... অপেক্ষা করুন...")
    
    for user_id in db['stats']['total_users']:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 **CINEFLIX Announcement:**\n\n{message}",
                parse_mode='Markdown'
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed broadcast to {user_id}: {e}")
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✔️ Sent: **{success}**\n"
        f"❌ Failed: **{failed}**\n\n"
        f"Total Reached: **{success}/{len(db['stats']['total_users'])}** users",
        parse_mode='Markdown'
    )

# ===================== CHANNEL POST HANDLER =====================
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-extract Message ID and notify admin"""
    message = update.channel_post
    
    if not message or message.chat.id != CHANNEL_ID:
        return
    
    # Check if video/document
    if message.video or message.document or message.animation:
        message_id = message.message_id
        
        # Get video details
        if message.video:
            file_name = message.video.file_name or "Unknown"
            file_size = f"{message.video.file_size / (1024*1024):.2f} MB"
            duration = f"{message.video.duration // 60}m {message.video.duration % 60}s"
            media_type = "🎬 Video"
        elif message.document:
            file_name = message.document.file_name or "Unknown"
            file_size = f"{message.document.file_size / (1024*1024):.2f} MB"
            duration = "N/A"
            media_type = "📄 Document"
        else:
            file_name = "Animation"
            file_size = f"{message.animation.file_size / (1024*1024):.2f} MB"
            duration = f"{message.animation.duration}s"
            media_type = "🎞️ Animation"
        
        # Create beautiful formatted message
        info_text = f"""
🎬 **New Video Uploaded!**

{media_type} uploaded to channel!

━━━━━━━━━━━━━━━━━━━━━
📋 **Message ID:** `{message_id}`

📝 **Google Sheet Formats:**
• Episode: `EP1:{message_id}`
• Full Movie: `Full:{message_id}`
• Part: `Part1:{message_id}`

━━━━━━━━━━━━━━━━━━━━━
📊 **File Details:**
📁 Name: `{file_name}`
💾 Size: `{file_size}`
⏱️ Duration: `{duration}`

━━━━━━━━━━━━━━━━━━━━━
💡 **Quick Copy:**
`EP1:{message_id}`

✅ **Video is now live!**
🔗 Channel: {CHANNEL_USERNAME}
        """
        
        try:
            # Send to admin personally
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=info_text,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Sent Message ID {message_id} notification to admin")
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")

# ===================== UTILITY COMMANDS =====================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    help_text = """
🎬 **CINEFLIX Video Bot Help**

**Commands:**
/start - Start bot
/help - Show this message

**How to Watch:**
1. Open CINEFLIX App
2. Select any video
3. Click "Watch Now"
4. Join required channels
5. Get your video!

**Support:**
Need help? Contact admin!

{CHANNEL_USERNAME}
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get chat/user ID"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        f"**IDs:*
