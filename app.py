import streamlit as st
import pandas as pd
import json
import os
from datetime import date, timedelta

st.set_page_config(page_title="Field Trip Communicator", layout="wide", page_icon="📅")

DATA_DIR = "data_ai"
TRIPS_FILE = f"{DATA_DIR}/field_trips.csv"
COMMS_FILE = f"{DATA_DIR}/communications.csv"
TEMPLATES_FILE = f"{DATA_DIR}/email_templates.json"
OFFSETS_FILE = f"{DATA_DIR}/comm_offsets.json"

os.makedirs(DATA_DIR, exist_ok=True)

GRADES = ["PreK", "Kindergarten", "1st Grade", "2nd Grade", "3rd Grade",
          "4th Grade", "5th Grade", "6th Grade", "7th Grade", "8th Grade"]

DEFAULT_COMM_TYPES = [
    "Initial Announcement",
    "Permission Slip Reminder",
    "Payment Reminder",
    "Day-Before Reminder"
]

DEFAULT_OFFSETS = {
    "Initial Announcement": 21,
    "Permission Slip Reminder": 14,
    "Payment Reminder": 7,
    "Day-Before Reminder": 1
}

DEFAULT_TEMPLATES = {
    "Initial Announcement": """Dear {grade} Families,

We are excited to announce that our class will be going on a field trip to {destination} on {trip_date}!

This is a wonderful educational opportunity for our students. More details about permission slips and payment will follow soon.

Please mark your calendars and feel free to reach out with any questions.

Warm regards,
[Your Name]""",

    "Permission Slip Reminder": """Dear {grade} Families,

A reminder that our upcoming field trip to {destination} is on {trip_date}.

Permission slips are due by {due_date}. Please return the signed form along with payment to ensure your child can participate.

Students without a signed permission slip will not be able to attend.

Thank you,
[Your Name]""",

    "Payment Reminder": """Dear {grade} Families,

This is a friendly reminder that our field trip to {destination} is just one week away on {trip_date}!

If you have not yet returned your child's permission slip and payment, please do so by {due_date}.

Please don't hesitate to reach out if you have any concerns — we want all students to participate.

Thank you,
[Your Name]""",

    "Day-Before Reminder": """Dear {grade} Families,

Just a reminder that tomorrow, {trip_date}, is our field trip to {destination}!

Please make sure your child:
• Arrives at school on time
• Wears comfortable clothing and shoes
• Brings a bag lunch (unless otherwise notified)
• Has sunscreen if needed

We are looking forward to a wonderful day! Feel free to reach out with any last-minute questions.

See you tomorrow,
[Your Name]"""
}

SAMPLE_TRIPS = [
    ("PreK", "Petting Zoo", "Happy Hollow Zoo & Farm"),
    ("PreK", "Story Time Walk", "City Botanical Garden"),
    ("Kindergarten", "Apple Picking", "Sunridge Farm"),
    ("Kindergarten", "Fire Station Visit", "Central Fire Station"),
    ("1st Grade", "Science Museum", "Discovery Science Center"),
    ("2nd Grade", "Nature Hike", "Regional Nature Park"),
    ("2nd Grade", "Aquarium Visit", "Bay Aquarium"),
    ("3rd Grade", "History Museum", "City History Museum"),
    ("4th Grade", "Planetarium", "Space Science Center"),
    ("4th Grade", "Farm to Table", "Green Valley Farm"),
    ("5th Grade", "Art Museum", "Metropolitan Art Gallery"),
    ("6th Grade", "Environmental Center", "Nature Reserve"),
    ("7th Grade", "Capitol Building Tour", "State Capitol"),
    ("7th Grade", "Tech Museum", "Innovation Museum"),
    ("8th Grade", "Graduation Trip", "Disneyland"),
]


def load_templates():
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_TEMPLATES.copy()


def save_templates(templates):
    with open(TEMPLATES_FILE, "w") as f:
        json.dump(templates, f, indent=2)


def load_offsets():
    if os.path.exists(OFFSETS_FILE):
        with open(OFFSETS_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_OFFSETS.copy()


def save_offsets(offsets):
    with open(OFFSETS_FILE, "w") as f:
        json.dump(offsets, f, indent=2)


def load_trips():
    if os.path.exists(TRIPS_FILE):
        df = pd.read_csv(TRIPS_FILE)
        df["trip_id"] = df["trip_id"].astype(int)
        if "num_students" not in df.columns:
            df["num_students"] = 0
        if "chaperones" not in df.columns:
            df["chaperones"] = ""
        df["num_students"] = df["num_students"].fillna(0).astype(int)
        df["chaperones"] = df["chaperones"].fillna("")
        return df
    today = date.today()
    rows = []
    for i, (grade, name, dest) in enumerate(SAMPLE_TRIPS):
        rows.append({
            "trip_id": i + 1,
            "grade": grade,
            "trip_name": name,
            "destination": dest,
            "trip_date": (today + timedelta(days=14 + i * 12)).strftime("%Y-%m-%d"),
            "num_students": 0,
            "chaperones": ""
        })
    df = pd.DataFrame(rows)
    df.to_csv(TRIPS_FILE, index=False)
    return df


def load_comms():
    if os.path.exists(COMMS_FILE):
        df = pd.read_csv(COMMS_FILE)
        df["trip_id"] = df["trip_id"].astype(int)
        df["comm_id"] = df["comm_id"].astype(int)
        return df
    return pd.DataFrame(columns=["comm_id", "trip_id", "comm_type", "send_date", "subject", "body"])


def save_trips(df):
    df.to_csv(TRIPS_FILE, index=False)


def save_comms(df):
    df.to_csv(COMMS_FILE, index=False)


def build_comms_for_trip(trip_row, offsets, templates):
    trip_date = pd.to_datetime(trip_row["trip_date"]).date()
    rows = []
    for comm_type in COMM_TYPES:
        offset = offsets.get(comm_type, DEFAULT_OFFSETS.get(comm_type, 14))
        send_date = trip_date - timedelta(days=offset)
        due_date = trip_date - timedelta(days=max(offset - 2, 1))
        template = templates.get(comm_type, DEFAULT_TEMPLATES[comm_type])
        try:
            body = template.format(
                grade=trip_row["grade"],
                destination=trip_row["destination"],
                trip_date=trip_date.strftime("%B %d, %Y"),
                due_date=due_date.strftime("%B %d, %Y")
            )
        except KeyError:
            body = template
        rows.append({
            "trip_id": int(trip_row["trip_id"]),
            "comm_type": comm_type,
            "send_date": send_date.strftime("%Y-%m-%d"),
            "subject": f"{comm_type}: {trip_row['trip_name']} — {trip_row['grade']}",
            "body": body
        })
    return rows


# ── Bootstrap data ────────────────────────────────────────────────────────────
trips_df = load_trips()
comms_df = load_comms()
templates = load_templates()
offsets = load_offsets()

# Sync: any template without an offset gets the default (14 days)
changed = False
for ct in list(templates.keys()):
    if ct not in offsets:
        offsets[ct] = DEFAULT_OFFSETS.get(ct, 14)
        changed = True
if changed:
    save_offsets(offsets)

# COMM_TYPES is always derived from what's saved — default types first, then custom
COMM_TYPES = [ct for ct in DEFAULT_COMM_TYPES if ct in templates] + \
             [ct for ct in templates if ct not in DEFAULT_COMM_TYPES]

existing_ids = set(comms_df["trip_id"].unique()) if not comms_df.empty else set()
new_rows = []
for _, trip in trips_df.iterrows():
    if int(trip["trip_id"]) not in existing_ids:
        new_rows.extend(build_comms_for_trip(trip, DEFAULT_OFFSETS, templates))

if new_rows:
    new_df = pd.DataFrame(new_rows)
    start_id = int(comms_df["comm_id"].max()) + 1 if not comms_df.empty else 1
    new_df["comm_id"] = range(start_id, start_id + len(new_df))
    comms_df = pd.concat([comms_df, new_df], ignore_index=True)
    save_comms(comms_df)

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📅 Field Trip Communicator")
st.sidebar.markdown(f"**Today:** {date.today().strftime('%B %d, %Y')}")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate to",
    ["🏠 Dashboard", "📋 Schedule by Grade", "✉️ Email Templates", "➕ Manage Field Trips"]
)

# ── Dashboard ─────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🏠 Field Trip Communication Dashboard")

    today = date.today()

    if comms_df.empty or trips_df.empty:
        st.info("No field trips found. Go to **Manage Field Trips** to add one.")
    else:
        merged = comms_df.merge(
            trips_df[["trip_id", "grade", "trip_name", "destination", "trip_date"]],
            on="trip_id", how="left"
        )
        merged["send_date"] = pd.to_datetime(merged["send_date"]).dt.date
        merged["trip_date"] = pd.to_datetime(merged["trip_date"]).dt.date
        merged = merged[merged["trip_date"] >= today]
        merged["days_until"] = merged["send_date"].apply(lambda d: (d - today).days)

        overdue = merged[merged["days_until"] < 0].sort_values("days_until")
        due_soon = merged[(merged["days_until"] >= 0) & (merged["days_until"] <= 7)].sort_values("days_until")
        upcoming = merged[(merged["days_until"] > 7) & (merged["days_until"] <= 30)].sort_values("days_until")

        c1, c2, c3 = st.columns(3)
        c1.metric("🔴 Overdue", len(overdue), help="Send these now!")
        c2.metric("🟡 Due This Week", len(due_soon))
        c3.metric("🟢 Next 30 Days", len(upcoming))

        def render_card(row):
            d = int(row["days_until"])
            if d < 0:
                badge = f"🔴 {abs(d)} day{'s' if abs(d) != 1 else ''} overdue"
            elif d == 0:
                badge = "🟠 Due TODAY"
            elif d <= 3:
                badge = f"🟡 Due in {d} day{'s' if d != 1 else ''}"
            else:
                badge = f"🟢 Due in {d} days"

            label = f"{badge}  |  {row['grade']} — {row['trip_name']}  |  {row['comm_type']}"
            with st.expander(label):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Send Date:** {row['send_date'].strftime('%B %d, %Y')}")
                col1.markdown(f"**Grade:** {row['grade']}")
                col2.markdown(f"**Trip Date:** {row['trip_date'].strftime('%B %d, %Y')}")
                col2.markdown(f"**Destination:** {row['destination']}")
                st.markdown("**Email Subject:**")
                st.code(row["subject"], language=None)
                st.markdown("**Email Body:**")
                st.text_area("Email Body", value=row["body"], height=220,
                             key=f"dash_{row['comm_id']}", disabled=True, label_visibility="collapsed")

        if not overdue.empty:
            st.subheader("🔴 Overdue — Send These Now!")
            for _, r in overdue.iterrows():
                render_card(r)

        if not due_soon.empty:
            st.subheader("🟡 Due This Week")
            for _, r in due_soon.iterrows():
                render_card(r)

        if not upcoming.empty:
            st.subheader("🟢 Coming Up (Next 30 Days)")
            for _, r in upcoming.iterrows():
                render_card(r)

        if overdue.empty and due_soon.empty and upcoming.empty:
            st.success("✅ All caught up! No communications due in the next 30 days.")

# ── Schedule by Grade ─────────────────────────────────────────────────────────
elif page == "📋 Schedule by Grade":
    st.title("📋 Communication Schedule by Grade")

    if trips_df.empty:
        st.info("No field trips added yet.")
    else:
        today = date.today()
        grade_filter = st.selectbox("Select Grade", ["All Grades"] + GRADES)

        filtered = trips_df if grade_filter == "All Grades" else trips_df[trips_df["grade"] == grade_filter]

        if filtered.empty:
            st.info(f"No trips found for {grade_filter}.")
        else:
            for _, trip in filtered.sort_values(["grade", "trip_date"]).iterrows():
                trip_date = pd.to_datetime(trip["trip_date"]).date()
                days_left = (trip_date - today).days

                if days_left < 0:
                    status = "✅ Past trip"
                elif days_left == 0:
                    status = "📍 Today!"
                else:
                    status = f"📅 In {days_left} days"

                st.subheader(f"{trip['grade']} — {trip['trip_name']}  ({status})")
                st.caption(f"Destination: {trip['destination']}   |   Trip Date: {trip_date.strftime('%B %d, %Y')}")

                trip_comms = comms_df[comms_df["trip_id"] == trip["trip_id"]].copy()
                if not trip_comms.empty:
                    trip_comms["send_date"] = pd.to_datetime(trip_comms["send_date"]).dt.date
                    trip_comms["Status"] = trip_comms["send_date"].apply(
                        lambda d: "🔴 Overdue" if d < today else ("🟠 Today" if d == today else "🟢 Upcoming")
                    )
                    display = trip_comms[["comm_type", "send_date", "Status"]].rename(columns={
                        "comm_type": "Email Type", "send_date": "Send Date"
                    })
                    st.dataframe(display, use_container_width=True, hide_index=True)
                st.markdown("---")

# ── Email Templates ───────────────────────────────────────────────────────────
elif page == "✉️ Email Templates":
    st.title("✉️ Email Templates")
    st.info("**Available placeholders:** `{grade}` · `{destination}` · `{trip_date}` · `{due_date}`")

    tab_edit_t, tab_add_t, tab_delete_t = st.tabs(["Edit Template", "Add New Template", "Delete Template"])

    with tab_edit_t:
        st.subheader("Edit an Existing Template")
        selected_type = st.selectbox("Select template to edit", COMM_TYPES, key="edit_tpl_select")

        col_info, col_schedule = st.columns([2, 1])
        with col_schedule:
            st.markdown("**Send schedule (days before trip)**")
            sched = [{"Email Type": k, "Days Before Trip": v} for k, v in offsets.items()]
            st.dataframe(pd.DataFrame(sched), use_container_width=True, hide_index=True)

        with col_info:
            current_body = templates.get(selected_type, DEFAULT_TEMPLATES.get(selected_type, ""))
            edited_body = st.text_area(f"Template body", value=current_body, height=320,
                                       key="edit_tpl_body")
            current_offset = offsets.get(selected_type, DEFAULT_OFFSETS.get(selected_type, 14))
            edited_offset = st.number_input("Days before trip to send this email",
                                            value=current_offset, min_value=1, max_value=90,
                                            key="edit_tpl_offset")

            c1, c2 = st.columns(2)
            if c1.button("💾 Save Changes", use_container_width=True, key="save_tpl"):
                templates[selected_type] = edited_body
                offsets[selected_type] = edited_offset
                save_templates(templates)
                save_offsets(offsets)
                st.success("Template saved!")

            if c2.button("↩️ Reset to Default", use_container_width=True, key="reset_tpl",
                         disabled=selected_type not in DEFAULT_TEMPLATES):
                templates[selected_type] = DEFAULT_TEMPLATES[selected_type]
                offsets[selected_type] = DEFAULT_OFFSETS[selected_type]
                save_templates(templates)
                save_offsets(offsets)
                st.rerun()

    with tab_add_t:
        st.subheader("Add a New Email Template")
        st.markdown("Create a custom email type that will be added to every field trip's communication schedule.")

        with st.form("add_template_form"):
            new_type_name = st.text_input("Template Name",
                                          placeholder="e.g., Chaperone Volunteer Request")
            new_offset = st.number_input("Days before trip to send this email",
                                         value=10, min_value=1, max_value=90)
            new_body = st.text_area("Email Body", height=300, placeholder="""Dear {grade} Families,

[Write your email here. You can use {grade}, {destination}, {trip_date}, and {due_date} as placeholders.]

Thank you,
[Your Name]""")
            add_tpl_btn = st.form_submit_button("➕ Add Template", use_container_width=True)

        if add_tpl_btn:
            name = new_type_name.strip()
            if not name:
                st.error("Please enter a template name.")
            elif name in templates:
                st.error(f'A template named "{name}" already exists. Use Edit Template to modify it.')
            elif not new_body.strip():
                st.error("Please enter an email body.")
            else:
                templates[name] = new_body.strip()
                offsets[name] = int(new_offset)
                save_templates(templates)
                save_offsets(offsets)
                st.success(f'✅ Template **"{name}"** added! It will appear in the communication '
                           f'schedule when you add or edit field trips.')
                st.rerun()

    with tab_delete_t:
        st.subheader("Delete a Custom Template")
        custom_types = [ct for ct in templates if ct not in DEFAULT_COMM_TYPES]
        if not custom_types:
            st.info("You have no custom templates to delete. Default templates cannot be deleted.")
        else:
            st.warning("Deleting a template does **not** remove already-scheduled emails for existing trips.")
            to_del = st.selectbox("Select template to delete", custom_types, key="del_tpl_select")
            if st.button("🗑️ Delete Template", type="secondary", key="del_tpl_btn"):
                templates.pop(to_del, None)
                offsets.pop(to_del, None)
                save_templates(templates)
                save_offsets(offsets)
                st.success(f'Template "{to_del}" deleted.')
                st.rerun()

# ── Manage Field Trips ────────────────────────────────────────────────────────
elif page == "➕ Manage Field Trips":
    st.title("➕ Manage Field Trips")

    tab_add, tab_edit, tab_view = st.tabs(["Add New Field Trip", "Edit Field Trip", "View / Delete Trips"])

    with tab_add:
        st.subheader("Add a New Field Trip")
        with st.form("add_trip"):
            c1, c2 = st.columns(2)
            grade = c1.selectbox("Grade", GRADES)
            trip_name = c2.text_input("Trip Name", placeholder="e.g., Science Museum")
            destination = st.text_input("Destination / Location", placeholder="e.g., Discovery Science Center")
            trip_date = st.date_input("Trip Date", min_value=date.today() + timedelta(days=1))

            c3, c4 = st.columns(2)
            num_students = c3.number_input("Number of Students", min_value=0, value=0, step=1)
            chaperones = c4.text_area("Teacher Chaperones", placeholder="e.g., Ms. Johnson, Mr. Lee",
                                      height=80, help="Enter names separated by commas")

            st.markdown("**Adjust communication schedule (days before trip):**")
            n_cols = min(len(COMM_TYPES), 4)
            off_cols = st.columns(n_cols)
            custom_offsets = {}
            for i, ct in enumerate(COMM_TYPES):
                custom_offsets[ct] = off_cols[i % n_cols].number_input(
                    ct, value=offsets.get(ct, DEFAULT_OFFSETS.get(ct, 14)),
                    min_value=1, max_value=90, key=f"off_{ct}"
                )

            submitted = st.form_submit_button("➕ Add Field Trip", use_container_width=True)

        if submitted:
            if not trip_name.strip() or not destination.strip():
                st.error("Please fill in Trip Name and Destination.")
            else:
                new_id = int(trips_df["trip_id"].max()) + 1 if not trips_df.empty else 1
                new_trip = {
                    "trip_id": new_id,
                    "grade": grade,
                    "trip_name": trip_name.strip(),
                    "destination": destination.strip(),
                    "trip_date": trip_date.strftime("%Y-%m-%d"),
                    "num_students": int(num_students),
                    "chaperones": chaperones.strip()
                }
                trips_df = pd.concat([trips_df, pd.DataFrame([new_trip])], ignore_index=True)
                save_trips(trips_df)

                new_comm_rows = build_comms_for_trip(new_trip, custom_offsets, templates)
                new_comm_df = pd.DataFrame(new_comm_rows)
                start_id = int(comms_df["comm_id"].max()) + 1 if not comms_df.empty else 1
                new_comm_df["comm_id"] = range(start_id, start_id + len(new_comm_df))
                comms_df = pd.concat([comms_df, new_comm_df], ignore_index=True)
                save_comms(comms_df)

                st.success(f"✅ **{trip_name}** added for **{grade}** on **{trip_date.strftime('%B %d, %Y')}**! "
                           f"4 email reminders have been scheduled.")
                st.rerun()

    with tab_edit:
        st.subheader("Edit an Existing Field Trip")
        if trips_df.empty:
            st.info("No field trips to edit yet.")
        else:
            edit_options = {
                f"{r['grade']} — {r['trip_name']} ({pd.to_datetime(r['trip_date']).strftime('%b %d, %Y')})": int(r["trip_id"])
                for _, r in trips_df.sort_values(["grade", "trip_date"]).iterrows()
            }
            selected_label = st.selectbox("Select a trip to edit", list(edit_options.keys()), key="edit_select")
            edit_id = edit_options[selected_label]
            trip_row = trips_df[trips_df["trip_id"] == edit_id].iloc[0]

            existing_comms = comms_df[comms_df["trip_id"] == edit_id].copy()
            existing_offsets = {}
            if not existing_comms.empty:
                existing_trip_date = pd.to_datetime(trip_row["trip_date"]).date()
                for _, cr in existing_comms.iterrows():
                    send = pd.to_datetime(cr["send_date"]).date()
                    existing_offsets[cr["comm_type"]] = (existing_trip_date - send).days

            with st.form("edit_trip"):
                c1, c2 = st.columns(2)
                edit_grade = c1.selectbox("Grade", GRADES, index=GRADES.index(trip_row["grade"]))
                edit_name = c2.text_input("Trip Name", value=trip_row["trip_name"])
                edit_dest = st.text_input("Destination / Location", value=trip_row["destination"])
                edit_date = st.date_input(
                    "Trip Date",
                    value=pd.to_datetime(trip_row["trip_date"]).date(),
                    min_value=date(2020, 1, 1)
                )

                c3, c4 = st.columns(2)
                edit_students = c3.number_input("Number of Students",
                                                min_value=0, step=1,
                                                value=int(trip_row.get("num_students", 0)))
                edit_chaperones = c4.text_area("Teacher Chaperones",
                                               value=str(trip_row.get("chaperones", "") or ""),
                                               height=80,
                                               help="Enter names separated by commas")

                st.markdown("**Communication schedule (days before trip):**")
                n_cols = min(len(COMM_TYPES), 4)
                off_cols = st.columns(n_cols)
                edit_offsets = {}
                for i, ct in enumerate(COMM_TYPES):
                    default_val = existing_offsets.get(ct, offsets.get(ct, DEFAULT_OFFSETS.get(ct, 14)))
                    edit_offsets[ct] = off_cols[i % n_cols].number_input(
                        ct, value=default_val, min_value=1, max_value=90, key=f"edit_off_{ct}"
                    )

                save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

            if save_btn:
                if not edit_name.strip() or not edit_dest.strip():
                    st.error("Please fill in Trip Name and Destination.")
                else:
                    trips_df.loc[trips_df["trip_id"] == edit_id, "grade"] = edit_grade
                    trips_df.loc[trips_df["trip_id"] == edit_id, "trip_name"] = edit_name.strip()
                    trips_df.loc[trips_df["trip_id"] == edit_id, "destination"] = edit_dest.strip()
                    trips_df.loc[trips_df["trip_id"] == edit_id, "trip_date"] = edit_date.strftime("%Y-%m-%d")
                    trips_df.loc[trips_df["trip_id"] == edit_id, "num_students"] = int(edit_students)
                    trips_df.loc[trips_df["trip_id"] == edit_id, "chaperones"] = edit_chaperones.strip()
                    save_trips(trips_df)

                    comms_df = comms_df[comms_df["trip_id"] != edit_id]
                    updated_trip = {
                        "trip_id": edit_id,
                        "grade": edit_grade,
                        "trip_name": edit_name.strip(),
                        "destination": edit_dest.strip(),
                        "trip_date": edit_date.strftime("%Y-%m-%d")
                    }
                    new_comm_rows = build_comms_for_trip(updated_trip, edit_offsets, templates)
                    new_comm_df = pd.DataFrame(new_comm_rows)
                    start_id = int(comms_df["comm_id"].max()) + 1 if not comms_df.empty else 1
                    new_comm_df["comm_id"] = range(start_id, start_id + len(new_comm_df))
                    comms_df = pd.concat([comms_df, new_comm_df], ignore_index=True)
                    save_comms(comms_df)

                    st.success(f"✅ **{edit_name}** updated! Email schedule has been regenerated.")
                    st.rerun()

    with tab_view:
        st.subheader("All Field Trips")
        if trips_df.empty:
            st.info("No field trips yet.")
        else:
            display = trips_df.copy()
            display["trip_date"] = pd.to_datetime(display["trip_date"]).dt.strftime("%B %d, %Y")
            display["num_students"] = display["num_students"].astype(int)
            display["chaperones"] = display["chaperones"].fillna("").astype(str)
            display = display.sort_values(["grade", "trip_date"])
            st.dataframe(
                display[["grade", "trip_name", "destination", "trip_date", "num_students", "chaperones"]].rename(columns={
                    "grade": "Grade", "trip_name": "Trip Name", "destination": "Destination",
                    "trip_date": "Trip Date", "num_students": "# Students", "chaperones": "Chaperones"
                }),
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.subheader("Delete a Field Trip")
            trip_options = {
                f"{r['grade']} — {r['trip_name']} ({pd.to_datetime(r['trip_date']).strftime('%b %d, %Y')})": int(r["trip_id"])
                for _, r in trips_df.iterrows()
            }
            to_delete = st.selectbox("Select trip to remove", list(trip_options.keys()))
            if st.button("🗑️ Delete This Trip", type="secondary"):
                del_id = trip_options[to_delete]
                trips_df = trips_df[trips_df["trip_id"] != del_id]
                comms_df = comms_df[comms_df["trip_id"] != del_id]
                save_trips(trips_df)
                save_comms(comms_df)
                st.success("Trip and its email schedule have been removed.")
                st.rerun()
