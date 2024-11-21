import plotly.figure_factory as ff
from datetime import datetime, timedelta
import logging
from textwrap import wrap
import plotly.graph_objects as go

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def generate_gantt_chart(tasks: list) -> go.Figure:
    """
    Creates a Gantt chart from a list of tasks
    """
    try:
        logger.info(f"Creating Gantt chart for {len(tasks)} tasks")
        
        # 1. Sort tasks by start date
        sorted_tasks = sorted(tasks, key=lambda x: datetime.strptime(x['start_date'], '%Y-%m-%d'))
        
        # 2. Prepare data for plotly
        df = []
        for task in sorted_tasks:
            df.append(dict(
                Task=task['name'],
                Start=task['start_date'],
                Finish=task['end_date'],
                Resource='Task'
            ))
            
        # 3. Create the Gantt chart
        fig = ff.create_gantt(
            df,
            colors={'Task': '#2980b9'},
            index_col='Resource',
            show_colorbar=False,
            group_tasks=True,
            showgrid_x=True,
            showgrid_y=True,
            bar_width=0.2,
        )
        
        # Get project date range
        start_date = min(datetime.strptime(task['start_date'], '%Y-%m-%d') for task in tasks)
        end_date = max(datetime.strptime(task['end_date'], '%Y-%m-%d') for task in tasks)
        
        # Generate month labels for the top of the chart
        current_date = start_date.replace(day=1)  # Start from first day of the month
        month_labels = []
        month_positions = []
        
        while current_date <= end_date:
            month_labels.append(current_date.strftime('%B %Y'))
            month_positions.append(current_date)
            # Move to first day of next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Add month labels as annotations at the top with better positioning
        annotations = []
        for label, pos in zip(month_labels, month_positions):
            annotations.append(dict(
                x=pos,
                y=1.15,  # Increased distance from top of chart
                xref='x',
                yref='paper',
                text=label,
                showarrow=False,
                font=dict(size=10),  # Slightly smaller font
                textangle=-45,
                xanchor='left',  # Align text to the left
                yanchor='bottom'  # Align text to the bottom
            ))
        
        # Add vertical lines for weeks and months
        current_date = start_date
        while current_date <= end_date:
            # Add dotted line for each Monday
            if current_date.weekday() == 0:
                fig.add_vline(
                    x=current_date,
                    line_dash="dot",
                    line_color="gray",
                    opacity=0.3
                )
            
            # Add solid line for first day of each month
            if current_date.day == 1:
                fig.add_vline(
                    x=current_date,
                    line_color="darkgray",
                    opacity=0.5
                )
            
            current_date += timedelta(days=1)
        
        # 4. Update layout for better visualization
        fig.update_layout(
            title='Project Timeline',
            height=max(800, len(tasks) * 65),
            font=dict(family='Arial, sans-serif'),
            xaxis=dict(
                title='',
                tickangle=45,
                tickformat='%B %Y',  # Show month names
                dtick='M1',  # Show tick for every month
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                side='bottom',
                showticklabels=True,  # Show bottom labels
                tickfont=dict(size=10)
            ),
            yaxis=dict(
                title='Tasks',
                tickmode='array',
                ticktext=[('<br>'.join(wrap(task['name'], width=35)) 
                          if len(task['name']) > 25 else task['name']) 
                          for task in reversed(sorted_tasks)],
                tickvals=list(range(len(tasks))),
                automargin=True,
                tickfont=dict(size=12)
            ),
            margin=dict(
                l=150,  # Left margin
                r=50,   # Right margin
                t=150,  # Top margin for upper month labels
                b=100   # Increased bottom margin for lower month labels
            ),
            showlegend=False,
            bargap=0.5,
            bargroupgap=0.2,
            plot_bgcolor='white',
            annotations=annotations
        )
        
        # 5. Add hover information
        fig.update_traces(
            opacity=0.8,
            hovertemplate='<b>%{text}</b><br>' +
                         'Start: %{base|%B %d, %Y}<br>' +
                         'End: %{x|%B %d, %Y}<extra></extra>'
        )
        
        logger.info("Gantt chart created successfully")
        return fig
            
    except Exception as e:
        logger.error(f"Error generating Gantt chart: {str(e)}", exc_info=True)
        raise