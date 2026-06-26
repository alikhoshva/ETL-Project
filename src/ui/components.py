import streamlit as st
import pandas as pd
import altair as alt
import os

def inject_custom_css():
    """Reads the custom styles from styles.css and injects them."""
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css")
    try:
        with open(css_path, "r") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Failed to load custom styles: {e}")

def render_kpi_card(title, value, subtitle=None, border_color="#6366F1"):
    """Renders a beautifully styled KPI card."""
    card_html = f"""
    <div class="kpi-card" style="border-left-color: {border_color};">
        <p class="kpi-title">{title}</p>
        <p class="kpi-value">{value}</p>
        {f'<p class="kpi-subtitle">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

def render_ingestion_quality_chart(ready_data, rejects_data):
    """Renders a 100% stacked horizontal bar chart showing valid vs. rejected proportions."""
    chart_data = []
    for name in ready_data.keys():
        valid_count = len(ready_data[name]['valid_df'])
        invalid_count = 0
        if name in rejects_data and 'invalid_df' in rejects_data[name]:
            invalid_count = len(rejects_data[name]['invalid_df'])
            
        chart_data.append({'Dataset': name, 'Status': 'Valid', 'Count': valid_count})
        chart_data.append({'Dataset': name, 'Status': 'Rejected', 'Count': invalid_count})
        
    df_chart = pd.DataFrame(chart_data)
    
    if not df_chart.empty and df_chart['Count'].sum() > 0:
        # Calculate percentages for tooltips
        totals = df_chart.groupby('Dataset')['Count'].transform('sum')
        df_chart['Percentage'] = df_chart['Count'] / totals
        
        color_scale = alt.Scale(
            domain=['Valid', 'Rejected'],
            range=['#6366F1', '#F43F5E']  # Premium Indigo and Soft Rose
        )
        
        chart = alt.Chart(df_chart).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('Dataset:N', title=None, axis=alt.Axis(labelFontSize=11)),
            x=alt.X('Count:Q', stack='normalize', title='Ingestion Quality Ratio', axis=alt.Axis(format='%', grid=True)),
            color=alt.Color('Status:N', scale=color_scale, legend=alt.Legend(title=None, orient="bottom", direction="horizontal")),
            tooltip=[
                'Dataset:N', 
                'Status:N', 
                alt.Tooltip('Count:Q', format=',', title='Record Count'),
                alt.Tooltip('Percentage:Q', format='.1%', title='Percentage')
            ]
        ).properties(
            height=250
        ).configure_view(
            strokeWidth=0
        )
        
        st.markdown("<h4 style='font-weight:600; margin-top: 15px; margin-bottom: 10px;'>📊 Pipeline Quality & Ingestion Balance</h4>", unsafe_allow_html=True)
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No records to visualize for ingestion quality.")

def render_welcome_screen():
    """Renders the dashboard welcome screen outlining system architecture."""
    st.markdown("""
    <div style="background-color: var(--secondary-background-color); padding: 30px; border-radius: 12px; border: 1px solid rgba(128,128,128,0.1); margin-top: 10px;">
        <h3 style="margin-top: 0; font-weight: 600;">👋 Welcome to the ETL Data Pipeline Control Center</h3>
        <p style="font-size: 1rem; line-height: 1.6;">
            This executive dashboard lets you orchestrate, inspect, and monitor the extraction, transformation, 
            and loading stages of movies metadata and production details.
        </p>
        <hr style="margin: 20px 0; border: none; border-top: 1px solid rgba(128,128,128,0.1); margin-top: 10px;">
        <h4 style="font-weight: 600; margin-bottom: 10px; color: #6366F1;">System Architecture Workflow</h4>
        <ol style="line-height: 1.8; margin-bottom: 25px; font-size: 0.95rem;">
            <li><strong>Extract Stage:</strong> Extracts raw movies data (CSV) and TMDB cached metadata (JSON) from file systems.</li>
            <li><strong>Transform Stage:</strong> Cleans schemas, verifies record integrity, manages anomalies, and performs relational joins.</li>
            <li><strong>Load Stage:</strong> Upserts data into the analytical staging views in PostgreSQL database, cataloging validation failures into <code>stg_rejects</code>.</li>
        </ol>
        <div style="background-color: rgba(99, 102, 241, 0.08); padding: 15px; border-radius: 8px; border-left: 4px solid #6366F1; font-size: 0.95rem;">
            <strong>💡 Get Started:</strong> Click <strong>"Process Data"</strong> in the left sidebar to execute the pipeline.
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_top_genres_chart(ready_data):
    """Renders the bar chart for the top genres from movies data."""
    if 'movies' in ready_data:
        movies_df = ready_data['movies']['valid_df']
        if 'genres' in movies_df.columns:
            st.markdown("<h4 style='font-weight:600;'>🎬 Top Movie Genres</h4>", unsafe_allow_html=True)
            genres_series = movies_df['genres'].dropna().str.split('|').explode()
            genres_series = genres_series[genres_series != ""]
            genre_counts = genres_series.value_counts().head(10).reset_index()
            genre_counts.columns = ['Genre', 'Count']
            if not genre_counts.empty:
                chart = alt.Chart(genre_counts).mark_bar(
                    color='#6366F1',
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4
                 ).encode(
                    x=alt.X('Genre:N', sort='-y', title=None, axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
                    y=alt.Y('Count:Q', title='Count'),
                    tooltip=['Genre', alt.Tooltip('Count', format=',')]
                ).properties(
                    height=280
                ).configure_view(
                    strokeWidth=0
                )
                st.altair_chart(chart, width="stretch")
            else:
                st.info("No genre data available.")

def render_budget_leaderboard(ready_data):
    """Renders the top highest-budget movies table."""
    if 'movies' in ready_data and 'tmdb_data' in ready_data:
        movies_df = ready_data['movies']['valid_df']
        tmdb_df = ready_data['tmdb_data']['valid_df']
        if 'tmdbId' in movies_df.columns and 'tmdbId' in tmdb_df.columns:
            merged = pd.merge(movies_df, tmdb_df, on='tmdbId', how='inner')
            if 'budget' in merged.columns and 'title' in merged.columns:
                merged['budget'] = pd.to_numeric(merged['budget'], errors='coerce')
                top_budget = merged.dropna(subset=['budget'])
                top_budget = top_budget[top_budget['budget'] > 0]
                top_budget = top_budget.sort_values(by='budget', ascending=False).head(5)
                if not top_budget.empty:
                    st.markdown("<h4 style='font-weight:600;'>💰 Top 5 Highest-Budget Movies</h4>", unsafe_allow_html=True)
                    top_budget_display = top_budget[['title', 'budget']].copy()
                    st.dataframe(
                        top_budget_display,
                        column_config={
                            "title": st.column_config.TextColumn("Movie Title"),
                            "budget": st.column_config.NumberColumn(
                                "Budget (USD)",
                                format="$%,.2f"
                            )
                        },
                        hide_index=True,
                        width="stretch"
                    )
                else:
                    st.info("No movie budget data available.")

@st.cache_data(ttl=10)
def get_enriched_view_data(data_uploaded):
    """Queries the enriched view from the database using a cached function."""
    from database import DatabaseLoader
    with DatabaseLoader() as loader:
        with loader.db_connection.cursor() as cursor:
            cursor.execute("SELECT * FROM movies_enriched_view LIMIT 10")
            colnames = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=colnames)

def render_db_view_tab(data_uploaded):
    """Renders the database view verification tab contents."""
    st.markdown("<h4 style='font-weight:600; margin-bottom: 15px;'>PostgreSQL View Verification</h4>", unsafe_allow_html=True)
    if data_uploaded:
        try:
            df_enriched = get_enriched_view_data(data_uploaded)
            if not df_enriched.empty:
                st.success("Successfully queried `movies_enriched_view` view from database!")
                st.dataframe(df_enriched, width="stretch")
            else:
                st.warning("The enriched view in database returned no records.")
        except Exception as e:
            st.error(f"Failed to query database view: {e}")
    else:
        st.info("Upload the processed data to the database using the control in the sidebar to activate this view verification.")

def render_logs_tab():
    """Renders the pipeline run logs with selection and searching/filtering."""
    st.markdown("<h4 style='font-weight:600; margin-bottom: 15px;'>Pipeline Run Logs</h4>", unsafe_allow_html=True)
    log_dir = "logs"
    if os.path.exists(log_dir):
        # List active logs, rotated backups, and legacy timestamped logs
        log_files = [
            f for f in os.listdir(log_dir) 
            if f.endswith(".log") or f.startswith("pipeline.log.") or f.startswith("errors.log.") or f.startswith("pipeline_") or f.startswith("errors_")
        ]
        # Sort: pipeline.log first, errors.log second, other .log files next, then backup logs
        log_files.sort(key=lambda x: (x != "pipeline.log", x != "errors.log", not x.endswith(".log"), x))
        
        if log_files:
            col_sel, col_space = st.columns([2, 2])
            with col_sel:
                selected_log = st.selectbox("Select log file to view", log_files, index=0)
            
            log_path = os.path.join(log_dir, selected_log)
            try:
                with open(log_path, "r") as f:
                    log_content = f.read()
                
                search_query = st.text_input("🔍 Search / Filter logs", placeholder="Type warning, error, info, or custom term...", key="log_search")
                
                lines = log_content.split('\n')
                if search_query:
                    filtered_lines = [line for line in lines if search_query.lower() in line.lower()]
                    st.caption(f"Showing {len(filtered_lines)} of {len(lines)} log lines.")
                    log_source = filtered_lines
                else:
                    log_source = lines
                    
                # Format lines as colored HTML divs inside terminal container
                import html
                display_lines = []
                for line in log_source:
                    if not line.strip():
                        continue
                    escaped_line = html.escape(line)
                    line_color = "#38BDF8"  # Default cyan
                    line_upper = line.upper()
                    if "ERROR" in line_upper or "CRITICAL" in line_upper or "EXCEPTION" in line_upper:
                        line_color = "#F43F5E"  # Soft rose/red
                    elif "WARNING" in line_upper:
                        line_color = "#F59E0B"  # Amber/yellow
                    elif "INFO" in line_upper:
                        line_color = "#94A3B8"  # Soft slate/gray
                    
                    display_lines.append(f'<div style="line-height: 1.5; margin-bottom: 3px; font-family: monospace; color: {line_color};">{escaped_line}</div>')
                
                display_html = "".join(display_lines)
                
                # Terminal box styling
                st.markdown(
                    f'<div class="terminal-container">{display_html}</div>', 
                    unsafe_allow_html=True
                )
                
                st.download_button(
                    label="📥 Download Log File",
                    data=log_content,
                    file_name=selected_log,
                    mime="text/plain",
                    width="stretch"
                )
            except Exception as e:
                st.error(f"Failed to read log file: {e}")
        else:
            st.info("No pipeline log files found in logs/ directory.")
    else:
        st.info("No logs directory found.")
