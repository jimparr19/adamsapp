import numpy as np
from datetime import datetime, timedelta

from bokeh.plotting import figure
from bokeh.models import Label, HoverTool, ColumnDataSource
from matplotlib import cm
import matplotlib.colors as colors


def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap


def plot_acc(acc_data, number_of_points, title):
    if len(acc_data['time']) > number_of_points:
        samples = np.linspace(0, len(acc_data['time']) - 1, number_of_points, dtype=int)
    else:
        samples = np.array(list(range(len(acc_data['time']))))

    p = figure(width=1000, plot_height=400, title=title,
               tools="pan,wheel_zoom,box_zoom,reset",
               x_axis_label='Time',
               y_axis_label='Acceleration (g)',
               logo=None,
               x_axis_type="datetime",
               )

    acc_datetime = list(map(lambda x: datetime.fromtimestamp(x), acc_data['time'][samples]))
    p.line(acc_datetime, acc_data['gX'][samples], color='#e74c3c', legend='gX')
    p.line(acc_datetime, acc_data['gY'][samples], color='#18bc9c', legend='gY')
    p.line(acc_datetime, acc_data['gZ'][samples], color='#3498db', legend='gZ')
    return p


def plot_scatter(left_data, right_data):
    number_of_windows = len(left_data)
    magnitude_ratio = np.array([])
    bilateral_magnitude = np.array([])
    left_activity = np.array([])
    right_activity = np.array([])
    for i_window in range(number_of_windows):
        left_svm = sum(np.sqrt(
            left_data[i_window]['gX'] ** 2 + left_data[i_window]['gY'] ** 2 + left_data[i_window]['gZ'] ** 2)) / len(
            left_data[i_window]['gX'])
        right_svm = sum(np.sqrt(
            right_data[i_window]['gX'] ** 2 + right_data[i_window]['gY'] ** 2 + right_data[i_window]['gZ'] ** 2)) / len(
            right_data[i_window]['gX'])
        bilateral_magnitude = np.append(bilateral_magnitude, left_svm+right_svm)
        if (right_svm/left_svm) > (left_svm/right_svm):
            magnitude_ratio = np.append(magnitude_ratio, (right_svm/left_svm)-1)
        else:
            magnitude_ratio = np.append(magnitude_ratio, -((left_svm/right_svm) - 1))

        left_activity = np.append(left_activity, left_svm)
        right_activity = np.append(right_activity, right_svm)

    xedges = np.linspace(-0.4, 0.4, 500)
    yedges = np.linspace(400, 700, 500)
    H, xedges, yedges = np.histogram2d(magnitude_ratio, bilateral_magnitude, bins=(xedges, yedges))
    x = np.array([])
    y = np.array([])
    c = np.array([])
    for i in range(H.shape[0]):
        for j in range(H.shape[1]):
            if H[i][j] > 0:
                c = np.append(c, H[i][j])
                x = np.append(x, xedges[i])
                y = np.append(y, yedges[j])
    colormap_orig = cm.viridis
    colormap = truncate_colormap(colormap_orig, minval=0.5, maxval=1.0)
    cmap_input = c / (max(c) - min(c))
    a_color = colormap(cmap_input, 1, True)
    bokeh_colors = ["#%02x%02x%02x" % (r, g, b) for r, g, b in a_color[:, 0:3]]
    x_lim = (-0.4, 0.4)
    y_lim = (400, 650)

    p = figure(width=1000, plot_height=1000, title='Symmetry',
               tools="pan,wheel_zoom,box_zoom,reset",
               x_axis_label='Magnitude ratio',
               y_axis_label='Bilateral magnitude',
               logo=None,
               x_range=x_lim,
               y_range=y_lim)

    p.scatter(x=x, y=y, fill_color=bokeh_colors, line_color=None, fill_alpha=0.6)

    left_text = Label(x=-0.3, y=600, text='left hand dominant', text_align='left')
    right_text = Label(x=0.3, y=600, text='right hand dominant', text_align='right')

    p.line([0, 0], y_lim, color='black')

    p.add_layout(left_text)
    p.add_layout(right_text)

    if (sum(right_activity) / sum(left_activity)) > (sum(right_activity) / sum(left_activity)):
        activity_ratio = (sum(right_activity)/sum(left_activity)) - 1
    else:
        activity_ratio = -((sum(left_activity) / sum(right_activity)) - 1)
    return p, activity_ratio


def plot_dashboard(all_sessions):
    start_time = np.array([])
    activity_ratio = np.array([])
    notes = []
    for session in all_sessions:
        start_time = np.append(start_time, session.start_time)
        activity_ratio = np.append(activity_ratio, session.activity_ratio)
        notes.append(session.notes)

    x_lim = (min(start_time) - timedelta(days=1), max(start_time) + timedelta(days=1))

    p = figure(width=1000, plot_height=400, title='Symmetry recovery',
               tools="hover,pan,wheel_zoom,box_zoom,reset",
               x_axis_label='Time',
               y_axis_label='Activity ratio',
               logo=None,
               x_axis_type="datetime",
               x_range=x_lim,
               )

    source = ColumnDataSource(data=dict(
        x=start_time,
        y=activity_ratio,
        notes=notes,
    ))

    p.circle(x='x', y='y', size=10, line_color='#3498db', fill_color='#18bc9c', source=source, name='scatter')
    hover = p.select(dict(type=HoverTool))
    hover.names = ['scatter']
    hover.tooltips = """<div> <span style"font-size: 15px; color: #333"> @notes </span></div>"""

    p.line(start_time, activity_ratio, line_width=2, line_color='#3498db')
    p.line(x_lim, [0, 0], color='#e74c3c', legend="target")
    return p

