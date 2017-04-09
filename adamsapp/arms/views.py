from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.layouts import layout

from .models import Session, DataFile
from .forms import AddDataForm, RemoveItemForm
from .cwa import CWA
from .process_data import aggregate_data, window_data
from .visualization import plot_acc, plot_scatter, plot_dashboard

import pickle
import os
import datetime
import numpy as np


def index(request):
    all_sessions = Session.objects.order_by('start_time')
    context = {'all_sessions': all_sessions}
    return render(request, "arms/index.html", context)


def add_session(request):
    new_session = Session()
    new_session.save()
    return redirect('add_data', session_id=new_session.id)


def save_session(request, session_id):
    this_session = Session.objects.get(id=session_id)
    if this_session.left_hand_file.count() == 0 or this_session.left_hand_file.count() == 0:
        this_session.delete()
    else:
        start_time = float('-inf')
        finish_time = float('inf')
        for file in this_session.left_hand_file.all():
            if file.start_time > start_time:
                start_time = file.start_time
            if file.finish_time < finish_time:
                finish_time = file.finish_time
        for file in this_session.right_hand_file.all():
            if file.start_time > start_time:
                start_time = file.start_time
            if file.finish_time < finish_time:
                finish_time = file.finish_time
        this_session.start_time_unix = start_time
        this_session.finish_time_unix = finish_time
        this_session.start_time = datetime.datetime.fromtimestamp(start_time)
        this_session.finish_time = datetime.datetime.fromtimestamp(finish_time)
        this_session.save()

    return redirect('arms_index')


def add_data(request, session_id):
    this_session = Session.objects.get(id=session_id)
    if request.POST:
        form = AddDataForm(request.POST, request.FILES)
        message = "No files uploaded."

        if form.is_valid():
            if 'datafile-left' in request.FILES:
                if request.FILES['datafile-left'].name.endswith('.cwa') or request.FILES['datafile-left'].name.endswith(
                        '.CWA'):
                    new_left = DataFile(raw_datafile=request.FILES['datafile-left'])
                    new_left.save()
                    session_data = Session.left_hand_file.through.objects.filter(session_id=session_id)
                    session_data.create(session_id=session_id, datafile_id=new_left.id)
                    data_array = CWA(new_left.raw_datafile.file.name.encode()).convert()
                    new_left.start_time = data_array['time'][0]
                    new_left.finish_time = data_array['time'][-1]
                    pickle_filename = new_left.raw_datafile.file.name.split('raw_data')[0] + 'processed_data' + \
                                      new_left.raw_datafile.file.name.split('raw_data')[1].split('.')[0] + '.p'
                    os.makedirs(os.path.dirname(pickle_filename), exist_ok=True)
                    pickle.dump(data_array, open(pickle_filename.encode(), 'wb'))
                    new_left.processed_datafile = pickle_filename
                    new_left.save()
                    del pickle_filename

                    message = "Data uploaded and processed OK."
                else:
                    message = "Not a cwa file"

            if 'datafile-right' in request.FILES:
                if request.FILES['datafile-right'].name.endswith('.cwa') or request.FILES['datafile-right'].name.endswith('.CWA'):
                    new_right = DataFile(raw_datafile=request.FILES['datafile-right'])
                    new_right.save()
                    session_data = Session.right_hand_file.through.objects.filter(session_id=session_id)
                    session_data.create(session_id=session_id, datafile_id=new_right.id)
                    data_array = CWA(new_right.raw_datafile.file.name.encode()).convert()
                    new_right.start_time = data_array['time'][0]
                    new_right.finish_time = data_array['time'][-1]
                    pickle_filename = new_right.raw_datafile.file.name.split('raw_data')[0] + 'processed_data' + \
                                      new_right.raw_datafile.file.name.split('raw_data')[1].split('.')[0] + '.p'
                    os.makedirs(os.path.dirname(pickle_filename), exist_ok=True)
                    pickle.dump(data_array, open(pickle_filename.encode(), 'wb'))
                    new_right.processed_datafile = pickle_filename
                    new_right.save()
                    del pickle_filename

                    message = "Data uploaded and processed OK."
                else:
                    message = "Not a cwa file"

            if 'datafile-notes' in request.POST:
                this_session.notes = request.POST['datafile-notes']
                this_session.save()
                message = "Notes uploaded."

            if request.is_ajax():
                return JsonResponse({'message': message})
            else:
                return redirect('add_data', session_id=session_id)
        else:
            if request.is_ajax():
                return JsonResponse({'message': message}, status=500)
            else:
                return redirect('add_data', session_id=session_id)

    else:
        form = AddDataForm()
        context = {'session': this_session,
                   'form': form, }
        return render(request, "arms/add_data.html", context)


def remove_datafile(request, session_id, file_id):
    this_data = DataFile.objects.get(id=file_id)
    this_data.delete()
    return redirect('add_data', session_id=session_id)


def remove_session(request, session_id):
    this_session = Session.objects.get(id=session_id)
    left_hand_files = this_session.left_hand_file.all()
    right_hand_files = this_session.right_hand_file.all()

    if request.POST:
        if left_hand_files:
            left_hand_files.delete()
        if right_hand_files:
            right_hand_files.delete()
        this_session.delete()

        return redirect('arms_index')

    else:
        form = RemoveItemForm(return_name=reverse('add_data', args=[session_id]))

    return render(request, 'arms/remove_session.html', {
        'session_id': session_id,
        'project': this_session,
        'left_hand_files': left_hand_files,
        'right_hand_files': right_hand_files,
        'form': form,
    })


def view_data(request, session_id):
    this_session = Session.objects.get(id=session_id)

    if this_session.view_div is None:
        left_hand_data_files = this_session.left_hand_file.all()
        right_hand_data_files = this_session.right_hand_file.all()

        left_hand_acc = aggregate_data(left_hand_data_files)
        right_hand_acc = aggregate_data(right_hand_data_files)

        p1 = plot_acc(left_hand_acc, 5000, 'Left hand')
        p2 = plot_acc(right_hand_acc, 5000, 'Right hand')

        start_time = this_session.start_time_unix
        finish_time = this_session.finish_time_unix
        windowed_left_hand_acc = window_data(left_hand_acc, start_time, finish_time, 1)
        windowed_right_hand_acc = window_data(right_hand_acc, start_time, finish_time, 1)
        p3, activity_ratio = plot_scatter(windowed_left_hand_acc, windowed_right_hand_acc)

        p = layout([[p1], [p2], [p3]])
        script, div = components(p)
        this_session.view_script = script
        this_session.view_div = div
        this_session.activity_ratio = activity_ratio
        this_session.save()
    else:
        script = this_session.view_script
        div = this_session.view_div

    return render(request, 'arms/view_data.html', {
        'session': this_session,
        'div': div,
        'script': script,
    })


def dashboard(request):
    all_sessions = Session.objects.order_by('start_time')
    p = plot_dashboard(all_sessions)
    script, div = components(p)

    return render(request, 'arms/dashboard.html', {
        'div': div,
        'script': script,
    })
