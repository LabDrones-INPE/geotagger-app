# Copyright (C) 2026 LABDRONES/INPE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.

# ==============================================================================
# Leaflet-Playback Integration
# Copyright (c) 2013, Nicholas Hallahan. All rights reserved.
# Licensed under BSD 2-Clause License (see LICENSE-THIRD-PARTY.txt)
# ==============================================================================

"""Standalone Application for Drone Geotagging Image Overview Using Leaflet-Playback Plugin"""


# --------------------------
#        Imports
# --------------------------
import PySimpleGUI as sg
import tkinter as tk
import os
import sys
from PIL import Image, ExifTags
from pathlib import Path
import matplotlib.colors as mcolors
import random
import pandas as pd
import datetime
import tempfile
import subprocess
import webbrowser
import numpy as np
import json
import shutil
from time import sleep
from contextlib import suppress
import ctypes

# Creates a hidden Tkinter instance to register the font for the global menu
root = tk.Tk()
root.withdraw()  # Hides the native Tkinter window.
root.option_add('*Menu.font', 'Helvetica 14 bold')  # Adjust the size (eg.: 12, 14)
root.option_add('*Menu.tearOff', False)  # Removes the native dotted line from the Linux menu

# Enables High DPI support in Windows to avoid small or blurry fonts
if sys.platform.startswith('win'):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


LEAFLET_PLAYBACK_LICENSE = """
Leaflet-Playback Plugin
Copyright (c) 2013, Nicholas Hallahan. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of
   conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list
   of conditions and the following disclaimer in the documentation and/or other materials
   provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED...
"""

WELLCOME_NOTICE = (
    "This work was supported by the Wellcome Trust, "
    "through grant number 224694/Z/21/Z."
)



#To handle with tqdm bug  when run aplication through a GUI no console interface
class NullWriter:
    def write(self, data):
        pass

# Override stdout and stderr with NullWriter in GUI --noconsole mode
# This allow to avoid a bug where tqdm try to write on NoneType
if sys.stdout is None:
    sys.stdout = NullWriter()

if sys.stderr is None:
    sys.stderr = NullWriter()

#Defines the exact color palette for the LabDrones app.
sg.LOOK_AND_FEEL_TABLE['LabDrones'] = {
    'BACKGROUND': '#f8f9fa',
    'TEXT': '#1a1a1a',
    'INPUT': '#ffffff',
    'TEXT_INPUT': '#1a1a1a',
    'SCROLL': '#16a085',
    'BUTTON': ('#ffffff', '#1a1a1a'), # Texto branco, botão escuro
    'PROGRESS': ('#16a085', '#e0e0e0'),
    'BORDER': 1,
    'SLIDER_DEPTH': 1,
    'PROGRESS_DEPTH': 0
}

# Apply custom theme
theme='LabDrones'
#theme='LightGrey1'
sg.theme(theme)   # Add colors to your windows


# Define stardard fonts
standard_font = ("Helvetica", 16, "bold")
button_font = ("Helvetica", 14, "bold")
text_font = ("Helvetica", 12, "bold")
multiline_text_font = ("Courier", 12)
reduced_text_font = ("Helvetica", 10, "bold")

# Set options
sg.set_options(font=standard_font)
use_custom_titlebar = False
title_name = 'LabDrones Geotagging Tool'


# Get screen size
screen_width, screen_height = sg.Window.get_screen_size()
height = int(screen_height * 0.9)
width = int(screen_width * 0.98)

# Set a proportional size for the modal window (e.g., 50% width and 60% height)
modal_width = int(screen_width * 0.50)
modal_height = int(screen_height * 0.60)

# Javascript file options
names_color = list(mcolors.CSS4_COLORS)
random.shuffle(names_color)

path_outputs = os.path.join(os.getcwd(),'geotagger_app-files-out')
os.makedirs(path_outputs, exist_ok=True)

fname_json = os.path.join(path_outputs,'overviews_performed.json')
if os.path.exists(fname_json):
    with open(fname_json,'r') as f_json:
        overviews_info = json.load(f_json)
else:
    overviews_info = {}

# Embedded Customized LeafletPlayBack plugin source code:
example_2_css = '#map {\n  position: absolute;\n  top: 0;\n  left: 0;\n  right: 0;\n  bottom: 0;\n}\n\n/* Suporta <footer class="lp"> ou div de controle direto */\nfooter.lp, .leaflet-control-playback, .lp {\n  position: fixed;\n  right: 0;\n  left: 0;\n  bottom: 10px;\n  z-index: 1000;\n}\n\n.lp .transport, .leaflet-control-playback .transport {\n  margin: 0 auto;\n  width: 768px;\n}\n\n.lp .navbar, .leaflet-control-playback .navbar {\n  margin-bottom: 0;\n}\n\n.lp .navbar-inner, .leaflet-control-playback .navbar-inner {\n  padding-right: 0;\n  padding-left: 0;\n}\n\n.lp #play-pause, .leaflet-control-playback #play-pause {\n  width: 18px;\n}\n\n.lp #speed-btn, .leaflet-control-playback #speed-btn {\n  width: 58px;\n}\n\n.lp .ui-slider, .leaflet-control-playback .ui-slider {\n  margin: 13px;\n}\n\n.lp #time-slider, .leaflet-control-playback #time-slider {\n  width: 370px;\n}\n\n.lp #calendar, .leaflet-control-playback #calendar {\n  margin: 5px;\n}\n\n.leaflet-control-layers-list {\n  margin-bottom: 0;\n}\n\n.lp .speed-menu, .leaflet-control-playback .speed-menu {\n  min-width: 60px;\n}\n\n.lp .dropdown-menu, .leaflet-control-playback .dropdown-menu {\n  padding: 5px;\n  text-align: center;\n}\n\n.lp #speed-slider, .leaflet-control-playback #speed-slider {\n  margin-left: auto;\n  margin-right: auto;\n}\n\n.lp .navbar .btn,\n.lp .navbar .btn-group,\n.leaflet-control-playback .navbar .btn,\n.leaflet-control-playback .navbar .btn-group {\n  margin-top: 0;\n  padding: 0;\n}\n\n.lp .navbar .nav > li > a.clock,\n.leaflet-control-playback .navbar .nav > li > a.clock {\n  padding: 0 3px 0 3px;\n  text-align: center;\n  margin-left: 4px;\n  margin-right: 4px;\n}\n\n.lp li.ctrl, .leaflet-control-playback li.ctrl {\n  background-color: #f5f5f5;\n  background-image: linear-gradient(to bottom, #ffffff, #e6e6e6);\n  border-right: 1px solid #d4d4d4;\n  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.05);\n}\n\n.lp .pull-right li.ctrl, .leaflet-control-playback .pull-right li.ctrl {\n  border-right: 0;\n  border-left: 1px solid #d4d4d4;\n}\n\n.lp li.ctrl:hover, .leaflet-control-playback li.ctrl:hover {\n  color: #333333;\n  text-decoration: none;\n  background-color: #e6e6e6;\n  background-position: 0 -15px;\n  transition: background-position 0.1s linear;\n}\n\n.lp li.ctrl:active, .leaflet-control-playback li.ctrl:active {\n  background-color: #e6e6e6;\n  outline: 0;\n  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.05);\n}\n\n/* Interrupções do Bootstrap no Leaflet */\ninput {\n  vertical-align: baseline;\n}\n\nlabel {\n  font-weight: bold;\n}\n\n/* Modificadores do Bootstrap */\n.navbar .nav { margin: 0; }\n\n.navbar .nav > li > .dropdown-menu:before,\n.bootstrap-timepicker-widget.dropdown-menu:before {\n  top: auto;\n  bottom: -7px;\n  border-top: 7px solid #ccc;\n  border-bottom: 0;\n  border-top-color: rgba(0, 0, 0, 0.2);\n}\n\n.navbar .nav > li > .dropdown-menu:after,\n.bootstrap-timepicker-widget.dropdown-menu:after {\n  top: auto;\n  bottom: -6px;\n  border-top: 6px solid #ffffff;\n  border-bottom: 0;\n}\n\n/* Correção de alinhamento para o Bootstrap 2 no Leaflet */\nfooter.lp {\n    display: block !important;\n    position: fixed !important;\n    bottom: 10px !important;\n    left: 0 !important;\n    right: 0 !important;\n    z-index: 9999 !important;\n    pointer-events: none; /* Permite clicar no mapa ao redor */\n}\n\nfooter.lp .transport {\n    pointer-events: auto; /* Mantém os botões do player clicáveis */\n    margin: 0 auto;\n    width: 768px;\n}\n\n/* Garante a exibição correta dos menus dropdown de velocidade e tempo */\n.lp .dropdown-menu {\n    z-index: 10000 !important;\n}'

fname_embedded_code = os.path.join(path_outputs,'example_2.css')
if not os.path.exists(fname_embedded_code):
    with open(fname_embedded_code,'w', encoding='utf-8') as fout:
        fout.write(example_2_css)

example_2_control_js = """L.Playback = L.Playback || {};

L.Playback.Control = L.Control.extend({

  _html: 
'<footer class="lp">' +
'  <div class="transport">' +
'    <div class="navbar">' +
'      <div class="navbar-inner">' +
'        <ul class="nav">' +
'          <li class="ctrl">' +
'            <a id="play-pause" href="#"><i id="play-pause-icon" class="fa fa-play fa-lg"></i></a>' +
'          </li>' +
'          <li class="ctrl dropup">' +
'            <a id="clock-btn" class="clock" data-toggle="dropdown" href="#">' +
'              <span id="cursor-date"></span><br/>' +
'              <span id="cursor-time"></span>' +
'            </a>' +
'            <div class="dropdown-menu" role="menu" aria-labelledby="clock-btn">' +
'              <label>Playback Cursor Time</label>' +
'              <div class="input-append bootstrap-timepicker">' +
'                <input id="timepicker" type="text" class="input-small span2">' +
'                <span class="add-on"><i class="fa fa-clock-o"></i></span>' +
'              </div>' +
'              <div id="calendar"></div>' +
'              <div class="input-append">' +
'                <input id="date-input" type="text" class="input-small">' +
'                <span class="add-on"><i class="fa fa-calendar"></i></span>' +
'              </div>' +
'            </div>' +
'          </li>' +
'        </ul>' +
'        <ul class="nav pull-right">' +
'          <li>' +
'            <div id="time-slider"></div>' +
'          </li>' +
'          <li class="ctrl dropup">' +
'            <a id="speed-btn" data-toggle="dropdown" href="#"><i class="fa fa-dashboard fa-lg"></i> <span id="speed-icon-val" class="speed">1</span>x</a>' +
'            <div class="speed-menu dropdown-menu" role="menu" aria-labelledby="speed-btn">' +
'              <label>Playback<br/>Speed</label>' +
'              <input id="speed-input" class="span1 speed" type="text" value="1" />' +
'              <div id="speed-slider"></div>' +
'            </div>' +
'          </li>' +
'          <li class="ctrl">' +
'            <a id="load-tracks-btn" href="#"><i class="fa fa-map-marker fa-lg"></i> Tracks</a>' +
'          </li>' +
'        </ul>' +
'      </div>' +
'    </div>' +
'  </div>' +
'</footer>' +
'<div id="load-tracks-modal" class="modal hide fade" tabindex="-1" role="dialog" aria-labelledby="load-tracks-label" aria-hidden="true">' +
'  <div class="modal-header">' +
'    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>' +
'    <h3 id="load-tracks-label">Load GPS Tracks</h3>' +
'  </div>' +
'  <div class="modal-body">' +
'    <p>' +
'      Leaflet Playback supports GeoJSON and GPX files!' +
'    </p>' +
'    <label>Upload a File</label>' +
'    <input type="file" id="load-tracks-file" />' +
'  </div>' +
'  <div class="modal-footer">' +
'    <button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>' +
'    <button id="load-tracks-save" class="btn btn-primary">Load</button>' +
'  </div>' +
'</div>',

  initialize: function(playback) {
    this.playback = playback;
    playback.addCallback(this._clockCallback);
  },

  onAdd: function(map) {
    var html = this._html;
    $('#map').after(html);
    this._setup();

    // just an empty container
    // TODO: dont do this
    return L.DomUtil.create('div');
  },

  _setup: function() {
    var self = this;
    var playback = this.playback;
    $('#play-pause').click(function() {
      if (playback.isPlaying() === false) {
        playback.start();
        $('#play-pause-icon').removeClass('fa-play');
        $('#play-pause-icon').addClass('fa-pause');
      } else {
        playback.stop();
        $('#play-pause-icon').removeClass('fa-pause');
        $('#play-pause-icon').addClass('fa-play');
      }
    });

    var startTime = playback.getStartTime();
    $('#cursor-date').html(L.Playback.Util.DateStr(startTime));
    $('#cursor-time').html(L.Playback.Util.TimeStr(startTime));

    $('#time-slider').slider({
      min: playback.getStartTime(),
      max: playback.getEndTime(),
      step: playback.getTickLen(),
      value: playback.getTime(),
      slide: function( event, ui ) {
        playback.setCursor(ui.value);
        $('#cursor-time').val(ui.value.toString());
        $('#cursor-time-txt').html(new Date(ui.value).toString());
      }
    });

    $('#speed-slider').slider({
      min: -9,
      max: 9,
      step: .5,
      value: self._speedToSliderVal(this.playback.getSpeed()),
      orientation: 'vertical',
      slide: function( event, ui ) {
        var speed = self._sliderValToSpeed(parseFloat(ui.value));
        playback.setSpeed(speed);
        $('.speed').html(speed).val(speed);
      }
    });

    $('#speed-input').on('keyup', function(e) {
      var speed = parseFloat($('#speed-input').val());
      if (!speed) return;
      playback.setSpeed(speed);
      $('#speed-slider').slider('value', speedToSliderVal(speed));
      $('#speed-icon-val').html(speed);
      if (e.keyCode === 13) {
        $('.speed-menu').dropdown('toggle');
      }
    });

    $('#calendar').datepicker({
      changeMonth: true,
      changeYear: true,
      altField: '#date-input',
      altFormat: 'mm/dd/yy',
      defaultDate: new Date(playback.getTime()),
      onSelect: function(date) {
        var date = new Date(date);
        var time = $('#timepicker').data('timepicker');
        var ts = self._combineDateAndTime(date, time);
        playback.setCursor(ts);
        $('#time-slider').slider('value', ts);
      }
    }); 

    $('#date-input').on('keyup', function(e) {
      $('#calendar').datepicker('setDate', $('#date-input').val());
    });

    $('.dropdown-menu').on('click', function(e) {
      e.stopPropagation();
    });

    $('#timepicker').timepicker({
      showSeconds: true
    });
    
    $('#timepicker').timepicker('setTime', 
        new Date(playback.getTime()).toTimeString());

    $('#timepicker').timepicker().on('changeTime.timepicker', function(e) {
      var date = $('#calendar').datepicker('getDate');
      var ts = self._combineDateAndTime(date, e.time);
      playback.setCursor(ts);
      $('#time-slider').slider('value', ts);
    });

    $('#load-tracks-btn').on('click', function(e) {
      $('#load-tracks-modal').modal();
    });

    $('#load-tracks-save').on('click', function(e) {
      var file = $('#load-tracks-file').get(0).files[0];
      self._loadTracksFromFile(file);
    });

  },

  _clockCallback: function(ms) {
    $('#cursor-date').html(L.Playback.Util.DateStr(ms));
    $('#cursor-time').html(L.Playback.Util.TimeStr(ms));
    $('#time-slider').slider('value', ms);
  },

  _speedToSliderVal: function(speed) {
    if (speed < 1) return -10+speed*10;
    return speed - 1;    
  },

  _sliderValToSpeed: function(val) {
    if (val < 0) return parseFloat((1+val/10).toFixed(2));
    return val + 1;    
  },

  _combineDateAndTime: function(date, time) {
    var yr = date.getFullYear();
    var mo = date.getMonth();
    var dy = date.getDate();
    // the calendar uses hour and the timepicker uses hours...
    var hr = time.hours || time.hour;
    if (time.meridian === 'PM' && hr !== 12) hr += 12;
    var min = time.minutes || time.minute;
    var sec = time.seconds || time.second;
    return new Date(yr, mo, dy, hr, min, sec).getTime();    
  },

  _loadTracksFromFile: function(file) {
    var self = this;
    
    if (!file) {
        alert('Por favor, selecione um arquivo para carregar.');
        return;
    }

    var reader = new FileReader();
    reader.readAsText(file);
    reader.onload = function(e) {
        var fileStr = e.target.result;
        var tracks = null;
        var isValid = false;

        /**
         * See if we can do GeoJSON...
         */
        try {
            var parsedJSON = JSON.parse(fileStr);
            // Checks if it is an array of tracks or a valid GeoJSON object (FeatureCollection, Feature, etc.)
            if (
                Array.isArray(parsedJSON) || 
                (parsedJSON && parsedJSON.type === 'FeatureCollection') ||
                (parsedJSON && parsedJSON.type === 'Feature') ||
                (parsedJSON && parsedJSON.geometry)
            ) {
                tracks = parsedJSON;
                isValid = true;
            }
        } catch (err) {
            // Ignore the JSON.parse error and try testing the GPX format below
        }

        /**
         * See if we can do GPX...
         */
        if (!isValid) {
            try {
                var parsedGPX = L.Playback.Util.ParseGPX(fileStr);
                if (parsedGPX) {
                    tracks = parsedGPX;
                    isValid = true;
                }
            } catch (err) {
                // Ignore the GPX error
            }
        }

        /**
         * If no format is valid, notify the user and stop.
         */
        if (!isValid || !tracks) {
            alert('Invalid file! The selected file is not a valid GeoJSON or GPX file.');
            console.error('Unable to load tracks: File format not supported or corrupted.');
            return;
        }

        // 4. Sucess: load the data and close modal
        self.playback.addData(tracks);
        $('#load-tracks-modal').modal('hide');
    };
  }
});
"""

fname_embedded_code = os.path.join(path_outputs,'example_2_control.js')
if not os.path.exists(fname_embedded_code):
    with open(fname_embedded_code,'w', encoding='utf-8') as fout:
        fout.write(example_2_control_js)

example_labdrones_js = """// Escopo global
var map = null;

$(function() {
    // 1. Defina os basemaps disponíveis
    var esriImagery = new L.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Esri, Maxar, Earthstar Geographics, and the GIS User Community'
    });

    // Camada de ruas/mapa base alternativo (OpenTopoMap - gratuito e sem API Key)
    var openStreetMap = new L.TileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        maxZoom: 17,
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
    });


    // 2. Inicialize o mapa com 'L.map' (m minúsculo)
    map = L.map('map', { 
        maxZoom: 20, 
        zoomControl: true,
        layers: [esriImagery] // Define o Esri World Imagery como padrão inicial
    });

    // 3. Crie o objeto com as opções de camadas base para o controle
    var baseLayers = {
        "Esri World Imagery": esriImagery,
        "OpenStreetMap": openStreetMap
    };

    // 4. Adicione o controle de camadas ao mapa no canto superior direito
    L.control.layers(baseLayers, null, { position: 'topright' }).addTo(map);

    // 5. Ajuste inicial de bounds ou centro
    if (typeof precalculatedBounds !== 'undefined') {    
        var bounds = L.latLngBounds(precalculatedBounds);
        map.fitBounds(bounds, { padding: [50, 50] });
    } else if (typeof center_map !== 'undefined' && typeof zoom_level !== 'undefined') {
        map.setView(center_map, zoom_level);
    } else {
        map.setView([-15.7801, -47.9292], 5);
    }

    // Adds scale to the map
    L.control.scale().addTo(map);   


    // =============== FUNÇÃO DO ÍCONE SVG DO DRONE =========
    function createDroneDivIcon(color, headingAngle = 0) {
        const svgIcon = `
            <svg class="drone-svg" width="36" height="36" viewBox="0 0 100 100" style="transform: rotate(${headingAngle}deg);">
                <!-- Quadcopter Body Frame -->
                <path d="M 30,30 L 70,70 M 70,30 L 30,70" stroke="${color}" stroke-width="6" stroke-linecap="round"/>
                <circle cx="50" cy="50" r="10" fill="${color}" stroke="#ffffff" stroke-width="3"/>
                
                <!-- Rotors -->
                <circle cx="30" cy="30" r="12" fill="none" stroke="#333333" stroke-width="3" stroke-dasharray="4,2"/>
                <circle cx="70" cy="30" r="12" fill="none" stroke="#333333" stroke-width="3" stroke-dasharray="4,2"/>
                <circle cx="30" cy="70" r="12" fill="none" stroke="#333333" stroke-width="3" stroke-dasharray="4,2"/>
                <circle cx="70" cy="70" r="12" fill="none" stroke="#333333" stroke-width="3" stroke-dasharray="4,2"/>
                
                <!-- Rotor Hubs -->
                <circle cx="30" cy="30" r="4" fill="#111111"/>
                <circle cx="70" cy="30" r="4" fill="#111111"/>
                <circle cx="30" cy="70" r="4" fill="#111111"/>
                <circle cx="70" cy="70" r="4" fill="#111111"/>

                <!-- Heading Direction Indicator Arrow -->
                <polygon points="50,22 43,36 57,36" fill="#ffffff" />
            </svg>
        `;

        return L.divIcon({
            html: svgIcon,
            className: 'drone-icon-container',
            iconSize: [36, 36],
            iconAnchor: [18, 18]
        });
    }

    var id = -1;
    var isUserInteracting = false;

    // Detecta se o usuário interagir livremente com o mapa
    map.on('dragstart zoomstart', function() {
        isUserInteracting = true;
    });



    var playbackOptions = {
        control: false,
        popups: true,
        orientIcons: true,
        speed: 8,

        timechange: function(time) {
            var activePositions = [];

            if (playback && playback._trackController) {
                var tracks = playback._trackController._tracks || [];
                
                tracks.forEach(function(track) {
                    var latLng = null;

                    if (track._marker && typeof track._marker.getLatLng === 'function') {
                        latLng = track._marker.getLatLng();
                    } else if (typeof track.getLatLng === 'function') {
                        latLng = track.getLatLng();
                    }

                    if (latLng && latLng.lat && latLng.lng) {
                        activePositions.push(latLng);
                    }
                });
            }

            // Centralização automática
            if (activePositions.length > 0 && !isUserInteracting) {
                if (activePositions.length === 1) {
                    var currentPos = activePositions[0];
                    if (map.getZoom() < 14) {
                        map.setView(currentPos, 16, { animate: true });
                    } else {
                        map.panTo(currentPos, { animate: true, duration: 0.2 });
                    }
                } else {
                    var activeBounds = L.latLngBounds(activePositions);
                    map.fitBounds(activeBounds, { padding: [60, 60], maxZoom: 16, animate: true });
                }
            }
        },

        layer: {
            pointToLayer: function(featureData, latlng) {
                var result = (featureData && featureData.properties && featureData.properties.path_options) 
                    ? featureData.properties.path_options 
                    : { radius: 5 };
                
                if (!result.radius) { result.radius = 5; }

                if (featureData && featureData.properties && featureData.properties.images) {
                    id += 1;
                    if (id === (featureData.properties.images.length - 1)) {
                        var id_tmp = id;
                        id = -1;
                        var imgUrl = featureData.properties.images[id_tmp];
                        if (imgUrl.search('.mp4') >= 0) {
                            return new L.CircleMarker(latlng, result).bindPopup(`<video width="800" autoplay><source src="${imgUrl}" type="video/mp4" /></video>`, {maxWidth : 800});
                        } else {
                            return new L.CircleMarker(latlng, result).bindPopup(`<a href="${imgUrl}" target="_blank"><img src="${imgUrl}" width="800px" height="600" /></a>`, {maxWidth : 800});
                        }
                    } else {
                        var imgUrl2 = featureData.properties.images[id];
                        if (imgUrl2.search('.mp4') >= 0) {
                            return new L.CircleMarker(latlng, result).bindPopup(`<video width="800" autoplay><source src="${imgUrl2}" type="video/mp4" /></video>`, {maxWidth : 800});
                        } else {
                            return new L.CircleMarker(latlng, result).bindPopup(`<a href="${imgUrl2}" target="_blank"><img src="${imgUrl2}" width="800px" height="600" /></a>`, {maxWidth : 800});
                        }
                    }
                } else {
                    return new L.CircleMarker(latlng, result);  
                }   
            }            
        },

        // ÍCONE DO Drone:
        marker: function (featureData) {
            // Tenta buscar a cor de path_options, de uma propriedade color direta, ou usa #FFCC00 como padrão
            var droneColor = '#FFCC00';
            
            if (featureData && featureData.properties) {
                if (featureData.properties.path_options && featureData.properties.path_options.color) {
                    droneColor = featureData.properties.path_options.color;
                } else if (featureData.properties.color) {
                    droneColor = featureData.properties.color;
                }
            }
            
            return {
                icon: createDroneDivIcon(droneColor, 0),
                getPopup: function (feature) {
                    if (feature && feature.properties) {
                        var title = feature.properties.title || (feature.properties.trk && feature.properties.trk.name) || "Drone Mission";
                        return '<b>' + title + '</b>';
                    }
                    return "Drone";
                }
            };
        }
    };


    // Inicialização da instância do Playback
    var playback = new L.Playback(map, labdronesTracks, null, playbackOptions);

    // Força o player a assumir a velocidade inicial 8
    if (typeof playback.setSpeed === 'function') {
        playback.setSpeed(8);
        
        // Aguarda os elementos do DOM do controle serem totalmente renderizados
        setTimeout(function() {
            // 1. Atualiza o campo de input de velocidade usando o ID exato (#speed-input)
            $('#speed-input').val(8).trigger('input').trigger('change');
            
            // 2. Atualiza o valor do rodapé usando o ID exato (#speed-icon-val)
            $('#speed-icon-val').text('8');
        }, 200);
    }


    // Injeção do Controle no Rodapé e Barra de Salto entre Voos
    var ControlClass = null;
    if (typeof L.Playback !== 'undefined' && L.Playback.Control) {
        ControlClass = L.Playback.Control;
    } else if (typeof L.PlayBack !== 'undefined' && L.PlayBack.Control) {
        ControlClass = L.PlayBack.Control;
    } else if (typeof L.Control.Playback === 'function') {
        ControlClass = L.Control.Playback;
    } else if (typeof L.Control.PlayBack === 'function') {
        ControlClass = L.Control.PlayBack;
    }

    if (ControlClass) {
        var controlOptions = { className: 'transport', controlClass: 'transport' };
        var playbackControl = new ControlClass(playback, controlOptions);
        
        $('footer.lp').remove();
        var $footer =$('<footer class="lp"></footer>');
        var controlDOM = playbackControl.onAdd(map);
        $footer.append(controlDOM);
        $('body').append($footer);

        // Função para realizar o salto temporal direto no início da track
        window.jumpToTrack = function(index) {
            if (labdronesTracks && labdronesTracks[index]) {
                var targetTrack = labdronesTracks[index];
                
                if (targetTrack.properties && targetTrack.properties.time && targetTrack.properties.time.length > 0) {
                    var startTime = targetTrack.properties.time[0];
                    
                    if (playback.setCursor) {
                        playback.setCursor(startTime);
                    } else if (playback.setTime) {
                        playback.setTime(startTime);
                    } else if (playback.clock) {
                        playback.clock.setTime(startTime);
                    }

                    if (playback._trackController && typeof playback._trackController.t === 'function') {
                        playback._trackController.t(startTime);
                    }

                    isUserInteracting = false;
                    var coords = targetTrack.geometry.coordinates[0];
                    map.setView([coords[1], coords[0]], 16, { animate: true });
                }
            }
        };

        // Renderiza os botões de atalho no rodapé
        var $trackSelector =$('<div class="track-jump-bar" style="text-align: center; margin-top: 5px; background: rgba(0,0,0,0.7); padding: 5px; border-radius: 4px;"></div>');
        labdronesTracks.forEach(function(track, idx) {
            var title = (track.properties && track.properties.title) ? track.properties.title.split(' ')[0] : 'Voo ' + (idx + 1);
            var $btn =$(`<button class="btn btn-mini btn-info" style="margin: 0 3px;" onclick="jumpToTrack(${idx})">✈️ ${title}</button>`);
            $trackSelector.append($btn);
        });
        $('footer.lp .transport').append($trackSelector);

        $('#time-slider').on('slidechange slide', function() {
            isUserInteracting = false; 
        });
    }
});
"""
fname_embedded_code = os.path.join(path_outputs,'example_labdrones.js')
if not os.path.exists(fname_embedded_code):
    with open(fname_embedded_code,'w', encoding='utf-8') as fout:
        fout.write(example_labdrones_js)

LeafletPlayBack_js = '// UMD initialization to work with CommonJS, AMD and basic browser script include\n(function (factory) {\n\tvar L;\n\tif (typeof define === \'function\' && define.amd) {\n\t\t// AMD\n\t\tdefine([\'leaflet\'], factory);\n\t} else if (typeof module === \'object\' && typeof module.exports === "object") {\n\t\t// Node/CommonJS\n\t\tL = require(\'leaflet\');\n\t\tmodule.exports = factory(L);\n\t} else {\n\t\t// Browser globals\n\t\tif (typeof window.L === \'undefined\')\n\t\t\tthrow \'Leaflet must be loaded first\';\n\t\tfactory(window.L);\n\t}\n}(function (L) {\n\nL.Playback = L.Playback || {};\n\nL.Playback.Util = L.Class.extend({\n  statics: {\n\n    DateStr: function(time) {\n      return new Date(time).toDateString();\n    },\n\n    TimeStr: function(time) {\n      var d = new Date(time);\n      var h = d.getHours();\n      var m = d.getMinutes();\n      var s = d.getSeconds();\n      var tms = time / 1000;\n      var dec = (tms - Math.floor(tms)).toFixed(2).slice(1);\n      var mer = \'AM\';\n      if (h > 11) {\n        h %= 12;\n        mer = \'PM\';\n      }\n      if (h === 0) h = 12;\n      if (m < 10) m = \'0\' + m;\n      if (s < 10) s = \'0\' + s;\n      return h + \':\' + m + \':\' + s + dec + \' \' + mer;\n    },\n\n    ParseGPX: function(gpx) {\n\n\t  var geojsonRoot = {\n        type: \'FeatureCollection\',\n\t\tfeatures : []\n      };\n\n\n\n      var xml = $.parseXML(gpx);\n\n      var trks = $(xml).find(\'trk\');\n      for (var trackIdx=0, numberOfTracks=trks.length; trackIdx<numberOfTracks; trackIdx++) {\n\n        var track = trks[trackIdx];\n        var geojson = {\n          type: \'Feature\',\n          geometry: {\n            type: \'MultiPoint\',\n            coordinates: []\n          },\n          properties: {\n            trk : {},\n            time: [],\n            speed: [],\n            altitude: [],\n            images: [],\n            bbox: []\n          }\n        };\n\n        geojson.properties.trk.name = $(track).find(\'name\').text();\n        geojson.properties.trk.desc = $(track).find(\'desc\').text();\n        geojson.properties.trk.type = $(track).find(\'type\').text();\n        geojson.properties.trk.src = $(track).find(\'src\').text();\n\n        var pts = $(track).find(\'trkpt\');\n        for (var i=0, len=pts.length; i<len; i++) {\n          var p = pts[i];\n          var lat = parseFloat(p.getAttribute(\'lat\'));\n          var lng = parseFloat(p.getAttribute(\'lon\'));\n          var timeStr = $(p).find(\'time\').text();\n          var eleStr = $(p).find(\'altit\').text();\n          var t = new Date(timeStr).getTime();\n          var ele = parseFloat(eleStr);\n          var img = $(p).find(\'images\').text();\n\n          var coords = geojson.geometry.coordinates;\n          var props = geojson.properties;\n\n          var time = props.time;\n          var altitude = geojson.properties.altitude;\n\n          coords.push([lng,lat]);\n          time.push(t);\n          altitude.push(ele);\n          images.push(img);\n        }\n        geojsonRoot.features.push(geojson);\n      }\n\n      return geojsonRoot;\n\n    }\n  }\n\n});\n\nL.Playback = L.Playback || {};\n\nL.Playback.MoveableMarker = L.Marker.extend({    \n    initialize: function (startLatLng, options, feature) {    \n        var marker_options = options.marker || {};\n\n        if (jQuery.isFunction(marker_options)){        \n            marker_options = marker_options(feature);\n        }\n        \n        L.Marker.prototype.initialize.call(this, startLatLng, marker_options);\n        \n        this.popupContent = \'\';\n        this.feature = feature;\n\t\t\n        if (marker_options.getPopup){\n            this.popupContent = marker_options.getPopup(feature);            \n        }\n        \n        if(options.popups)\n        {\n            this.bindPopup(this.getPopupContent() + startLatLng.toString());\n        }\n        \t\n        if(options.labels)\n        {\n            if(this.bindLabel)\n            {\n                this.bindLabel(this.getPopupContent());\n            }\n            else\n            {\n                console.log("Label binding requires leaflet-label (https://github.com/Leaflet/Leaflet.label)");\n            }\n        }\n    },\n    \n    getPopupContent: function() {\n        if (this.popupContent !== \'\'){\n            return \'<b>\' + this.popupContent + \'</b><br/>\';\n        }\n        \n        return \'\';\n    },\n\n    move: function (latLng, transitionTime) {\n        // Only if CSS3 transitions are supported\n        if (L.DomUtil.TRANSITION) {\n            if (this._icon) { \n                this._icon.style[L.DomUtil.TRANSITION] = \'all \' + transitionTime + \'ms linear\'; \n                if (this._popup && this._popup._wrapper)\n                    this._popup._wrapper.style[L.DomUtil.TRANSITION] = \'all \' + transitionTime + \'ms linear\'; \n            }\n            if (this._shadow) { \n                this._shadow.style[L.DomUtil.TRANSITION] = \'all \' + transitionTime + \'ms linear\'; \n            }\n        }\n        this.setLatLng(latLng);\n        if (this._popup) {\n            this._popup.setContent(this.getPopupContent() + this._latlng.toString());\n        }    \n    },\n    \n    // modify leaflet markers to add our roration code\n    /*\n     * Based on comments by @runanet and @coomsie \n     * https://github.com/CloudMade/Leaflet/issues/386\n     *\n     * Wrapping function is needed to preserve L.Marker.update function\n     */\n    _old__setPos:L.Marker.prototype._setPos,\n    \n    _updateImg: function (i, a, s) {\n        a = L.point(s).divideBy(2)._subtract(L.point(a));\n        var transform = \'\';\n        transform += \' translate(\' + -a.x + \'px, \' + -a.y + \'px)\';\n        transform += \' rotate(\' + this.options.iconAngle + \'deg)\';\n        transform += \' translate(\' + a.x + \'px, \' + a.y + \'px)\';\n        i.style[L.DomUtil.TRANSFORM] += transform;\n    },\n    setIconAngle: function (iconAngle) {\n        this.options.iconAngle = iconAngle;\n        if (this._map)\n            this.update();\n    },\n    _setPos: function (pos) {\n        if (this._icon) {\n            this._icon.style[L.DomUtil.TRANSFORM] = "";\n        }\n        if (this._shadow) {\n            this._shadow.style[L.DomUtil.TRANSFORM] = "";\n        }\n\n        this._old__setPos.apply(this, [pos]);\n        if (this.options.iconAngle) {\n            var a = this.options.icon.options.iconAnchor;\n            var s = this.options.icon.options.iconSize;\n            var i;\n            if (this._icon) {\n                i = this._icon;\n                this._updateImg(i, a, s);\n            }\n\n            if (this._shadow) {\n                // Rotate around the icons anchor.\n                s = this.options.icon.options.shadowSize;\n                i = this._shadow;\n                this._updateImg(i, a, s);\n            }\n\n        }\n    }\n});\n\nL.Playback = L.Playback || {};\n\n\n        \nL.Playback.Track = L.Class.extend({\n\n        initialize : function (geoJSON, options) {\n            options = options || {};\n            var tickLen = options.tickLen || 250;\n            this._staleTime = options.staleTime || 60*60*1000;\n            this._fadeMarkersWhenStale = options.fadeMarkersWhenStale || false;\n            \n            this._geoJSON = geoJSON;\n            this._tickLen = tickLen;\n            this._ticks = [];\n            this._marker = null;\n\t\t\tthis._orientations = [];\n\t\t\t\n            var sampleTimes = geoJSON.properties.time;\n\t\t\t\n            this._orientIcon = options.orientIcons;\n            var previousOrientation;\n\t\t\t\n            var samples = geoJSON.geometry.coordinates;\n            var currSample = samples[0];\n            var nextSample = samples[1];\n\t\t\t\n            var currSampleTime = sampleTimes[0];\n            var t = currSampleTime;  // t is used to iterate through tick times\n            var nextSampleTime = sampleTimes[1];\n            var tmod = t % tickLen; // ms past a tick time\n            var rem,\n            ratio;\n\n            // handle edge case of only one t sample\n            if (sampleTimes.length === 1) {\n                if (tmod !== 0)\n                    t += tickLen - tmod;\n                this._ticks[t] = samples[0];\n\t\t\t\tthis._orientations[t] = 0;\n                this._startTime = t;\n                this._endTime = t;\n                return;\n            }\n\n            // interpolate first tick if t not a tick time\n            if (tmod !== 0) {\n                rem = tickLen - tmod;\n                ratio = rem / (nextSampleTime - currSampleTime);\n                t += rem;\n                this._ticks[t] = this._interpolatePoint(currSample, nextSample, ratio);\n\t\t\t\tthis._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                previousOrientation = this._orientations[t];\n            } else {\n                this._ticks[t] = currSample;\n\t\t\t\tthis._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                previousOrientation = this._orientations[t];\n            }\n\n            this._startTime = t;\n            t += tickLen;\n            while (t < nextSampleTime) {\n                ratio = (t - currSampleTime) / (nextSampleTime - currSampleTime);\n                this._ticks[t] = this._interpolatePoint(currSample, nextSample, ratio);\n\t\t\t\tthis._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                previousOrientation = this._orientations[t];\n                t += tickLen;\n            }\n\n            // iterating through the rest of the samples\n            for (var i = 1, len = samples.length; i < len; i++) {\n                currSample = samples[i];\n                nextSample = samples[i + 1];\n                t = currSampleTime = sampleTimes[i];\n                nextSampleTime = sampleTimes[i + 1];\n\n                tmod = t % tickLen;\n                if (tmod !== 0 && nextSampleTime) {\n                    rem = tickLen - tmod;\n                    ratio = rem / (nextSampleTime - currSampleTime);\n                    t += rem;\n                    this._ticks[t] = this._interpolatePoint(currSample, nextSample, ratio);\n\t\t\t\t\tif(nextSample){\n                        this._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                        previousOrientation = this._orientations[t];\n                    } else {\n                        this._orientations[t] = previousOrientation;    \n                    }\n                } else {\n                    this._ticks[t] = currSample;\n                    if(nextSample){\n                        this._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                        previousOrientation = this._orientations[t];\n                    } else {\n                        this._orientations[t] = previousOrientation;    \n                    }\n                }\n\n                t += tickLen;\n                while (t < nextSampleTime) {\n                    ratio = (t - currSampleTime) / (nextSampleTime - currSampleTime);\n                    \n                    if (nextSampleTime - currSampleTime > options.maxInterpolationTime){\n                        this._ticks[t] = currSample;\n                        \n\t\t\t\t\t\tif(nextSample){\n                            this._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                            previousOrientation = this._orientations[t];\n                        } else {\n                            this._orientations[t] = previousOrientation;    \n                        }\n                    }\n                    else {\n                        this._ticks[t] = this._interpolatePoint(currSample, nextSample, ratio);\n\t\t\t\t\t\tif(nextSample) {\n                            this._orientations[t] = this._directionOfPoint(currSample,nextSample);\n                            previousOrientation = this._orientations[t];\n                        } else {\n                            this._orientations[t] = previousOrientation;    \n                        }\n                    }\n                    \n                    t += tickLen;\n                }\n            }\n\n            // the last t in the while would be past bounds\n            this._endTime = t - tickLen;\n            this._lastTick = this._ticks[this._endTime];\n\n        },\n\n        _interpolatePoint : function (start, end, ratio) {\n            try {\n                var delta = [end[0] - start[0], end[1] - start[1]];\n                var offset = [delta[0] * ratio, delta[1] * ratio];\n                return [start[0] + offset[0], start[1] + offset[1]];\n            } catch (e) {\n                console.log(\'err: cant interpolate a point\');\n                console.log([\'start\', start]);\n                console.log([\'end\', end]);\n                console.log([\'ratio\', ratio]);\n            }\n        },\n        \n        _directionOfPoint:function(start,end){\n            return this._getBearing(start[1],start[0],end[1],end[0]);\n        },\n        \n        _getBearing:function(startLat,startLong,endLat,endLong){\n              startLat = this._radians(startLat);\n              startLong = this._radians(startLong);\n              endLat = this._radians(endLat);\n              endLong = this._radians(endLong);\n\n              var dLong = endLong - startLong;\n\n              var dPhi = Math.log(Math.tan(endLat/2.0+Math.PI/4.0)/Math.tan(startLat/2.0+Math.PI/4.0));\n              if (Math.abs(dLong) > Math.PI){\n                if (dLong > 0.0)\n                   dLong = -(2.0 * Math.PI - dLong);\n                else\n                   dLong = (2.0 * Math.PI + dLong);\n              }\n\n              return (this._degrees(Math.atan2(dLong, dPhi)) + 360.0) % 360.0;\n        },\n        \n        _radians:function(n) {\n          return n * (Math.PI / 180);\n        },\n        _degrees:function(n) {\n          return n * (180 / Math.PI);\n        },\n\n        getFirstTick : function () {\n            return this._ticks[this._startTime];\n        },\n\n        getLastTick : function () {\n            return this._ticks[this._endTime];\n        },\n\n        getStartTime : function () {\n            return this._startTime;\n        },\n\n        getEndTime : function () {\n            return this._endTime;\n        },\n\n        getTickMultiPoint : function () {\n            var t = this.getStartTime();\n            var endT = this.getEndTime();\n            var coordinates = [];\n            var time = [];\n            while (t <= endT) {\n                time.push(t);\n                coordinates.push(this.tick(t));\n                t += this._tickLen;\n            }\n\n            return {\n                type : \'Feature\',\n                geometry : {\n                    type : \'MultiPoint\',\n                    coordinates : coordinates\n                },\n                properties : {\n                    time : time\n                }\n            };\n        },\n\t\t\n        trackPresentAtTick : function(timestamp)\n        {\n            return (timestamp >= this._startTime);\n        },\n        \n        trackStaleAtTick : function(timestamp)\n        {\n            return ((this._endTime + this._staleTime) <= timestamp);\n        },\n\n        tick : function (timestamp) {\n            if (timestamp > this._endTime)\n                timestamp = this._endTime;\n            if (timestamp < this._startTime)\n                timestamp = this._startTime;\n            return this._ticks[timestamp];\n        },\n\t\t\n        courseAtTime: function(timestamp)\n        {\n            //return 90;\n            if (timestamp > this._endTime)\n               timestamp = this._endTime;\n            if (timestamp < this._startTime)\n                timestamp = this._startTime;\n            return this._orientations[timestamp];\n        },\n        \n        setMarker : function(timestamp, options){\n            var lngLat = null;\n            \n            // if time stamp is not set, then get first tick\n            if (timestamp) {\n                lngLat = this.tick(timestamp);\n            }\n            else {\n                lngLat = this.getFirstTick();\n            }        \n        \n            if (lngLat) {\n                var latLng = new L.LatLng(lngLat[1], lngLat[0]);\n                this._marker = new L.Playback.MoveableMarker(latLng, options, this._geoJSON);     \n\t\t\t\tif(options.mouseOverCallback) {\n                    this._marker.on(\'mouseover\',options.mouseOverCallback);\n                }\n\t\t\t\tif(options.clickCallback) {\n                    this._marker.on(\'click\',options.clickCallback);\n                }\n\t\t\t\t\n\t\t\t\t//hide the marker if its not present yet and fadeMarkersWhenStale is true\n\t\t\t\tif(this._fadeMarkersWhenStale && !this.trackPresentAtTick(timestamp))\n\t\t\t\t{\n\t\t\t\t\tthis._marker.setOpacity(0);\n\t\t\t\t}\n            }\n            \n            return this._marker;\n        },\n        \n        moveMarker : function(latLng, transitionTime,timestamp) {\n            if (this._marker) {\n                if(this._fadeMarkersWhenStale) {\n                    //show the marker if its now present\n                    if(this.trackPresentAtTick(timestamp)) {\n                        this._marker.setOpacity(1);\n                    } else {\n                        this._marker.setOpacity(0);\n                    }\n                    \n                    if(this.trackStaleAtTick(timestamp)) {\n                        this._marker.setOpacity(0.25);\n                    }\n                }\n\t\t\t\t\n                if(this._orientIcon){\n                    this._marker.setIconAngle(this.courseAtTime(timestamp));\n                }\n\t\t\t\t\n                this._marker.move(latLng, transitionTime);\n            }\n        },\n        \n        getMarker : function() {\n            return this._marker;\n        }\n\n    });\n\nL.Playback = L.Playback || {};\n\nL.Playback.TrackController = L.Class.extend({\n\n    initialize : function (map, tracks, options) {\n        this.options = options || {};\n    \n        this._map = map;\n\n        this._tracks = [];\n\n        // initialize tick points\n        this.setTracks(tracks);\n    },\n    \n    clearTracks: function(){\n        while (this._tracks.length > 0) {\n            var track = this._tracks.pop();\n            var marker = track.getMarker();\n            \n            if (marker){\n                this._map.removeLayer(marker);\n            }\n        }            \n    },\n\n    setTracks : function (tracks) {\n        // reset current tracks\n        this.clearTracks();\n        \n        this.addTracks(tracks);\n    },\n    \n    addTracks : function (tracks) {\n        // return if nothing is set\n        if (!tracks) {\n            return;\n        }\n        \n        if (tracks instanceof Array) {            \n            for (var i = 0, len = tracks.length; i < len; i++) {\n                this.addTrack(tracks[i]);\n            }\n        } else {\n            this.addTrack(tracks);\n        }            \n    },\n    \n    // add single track\n    addTrack : function (track, timestamp) {\n        // return if nothing is set\n        if (!track) {\n            return;\n        }\n\n        var marker = track.setMarker(timestamp, this.options);\n\n        if (marker) {\n            marker.addTo(this._map);\n            \n            this._tracks.push(track);\n        }            \n    },\n\n    tock : function (timestamp, transitionTime) {\n        for (var i = 0, len = this._tracks.length; i < len; i++) {\n            var lngLat = this._tracks[i].tick(timestamp);\n            var latLng = new L.LatLng(lngLat[1], lngLat[0]);\n            this._tracks[i].moveMarker(latLng, transitionTime,timestamp);\n        }\n    },\n\n    getStartTime : function () {\n        var earliestTime = 0;\n\n        if (this._tracks.length > 0) {\n            earliestTime = this._tracks[0].getStartTime();\n            for (var i = 1, len = this._tracks.length; i < len; i++) {\n                var t = this._tracks[i].getStartTime();\n                if (t < earliestTime) {\n                    earliestTime = t;\n                }\n            }\n        }\n        \n        return earliestTime;\n    },\n\n    getEndTime : function () {\n        var latestTime = 0;\n    \n        if (this._tracks.length > 0){\n            latestTime = this._tracks[0].getEndTime();\n            for (var i = 1, len = this._tracks.length; i < len; i++) {\n                var t = this._tracks[i].getEndTime();\n                if (t > latestTime) {\n                    latestTime = t;\n                }\n            }\n        }\n    \n        return latestTime;\n    },\n\n    getTracks : function () {\n        return this._tracks;\n    }\n});\nL.Playback = L.Playback || {};\n\nL.Playback.Clock = L.Class.extend({\n\n  initialize: function (trackController, callback, options) {\n    this._trackController = trackController;\n    this._callbacksArry = [];\n    if (callback) this.addCallback(callback);\n    L.setOptions(this, options);\n    this._speed = this.options.speed;\n    this._tickLen = this.options.tickLen;\n    this._cursor = trackController.getStartTime();\n    this._transitionTime = this._tickLen / this._speed;\n  },\n\n  _tick: function (self) {\n    if (self._cursor > self._trackController.getEndTime()) {\n      clearInterval(self._intervalID);\n      return;\n    }\n    self._trackController.tock(self._cursor, self._transitionTime);\n    self._callbacks(self._cursor);\n    self._cursor += self._tickLen;\n  },\n\n  _callbacks: function(cursor) {\n    var arry = this._callbacksArry;\n    for (var i=0, len=arry.length; i<len; i++) {\n      arry[i](cursor);\n    }\n  },\n\n  addCallback: function(fn) {\n    this._callbacksArry.push(fn);\n  },\n\n  start: function () {\n    if (this._intervalID) return;\n    this._intervalID = window.setInterval(\n      this._tick, \n      this._transitionTime, \n      this);\n  },\n\n  stop: function () {\n    if (!this._intervalID) return;\n    clearInterval(this._intervalID);\n    this._intervalID = null;\n  },\n\n  getSpeed: function() {\n    return this._speed;\n  },\n\n  isPlaying: function() {\n    return this._intervalID ? true : false;\n  },\n\n  setSpeed: function (speed) {\n    this._speed = speed;\n    this._transitionTime = this._tickLen / speed;\n    if (this._intervalID) {\n      this.stop();\n      this.start();\n    }\n  },\n\n  setCursor: function (ms) {\n    var time = parseInt(ms);\n    if (!time) return;\n    var mod = time % this._tickLen;\n    if (mod !== 0) {\n      time += this._tickLen - mod;\n    }\n    this._cursor = time;\n    this._trackController.tock(this._cursor, 0);\n    this._callbacks(this._cursor);\n  },\n\n  getTime: function() {\n    return this._cursor;\n  },\n\n  getStartTime: function() {\n    return this._trackController.getStartTime();\n  },\n\n  getEndTime: function() {\n    return this._trackController.getEndTime();\n  },\n\n  getTickLen: function() {\n    return this._tickLen;\n  }\n\n});\n\n// Simply shows all of the track points as circles.\n// TODO: Associate circle color with the marker color.\n\nL.Playback = L.Playback || {};\n\nL.Playback.TracksLayer = L.Class.extend({\n    initialize : function (map, options) {\n        var layer_options = options.layer || {};\n        \n        if (jQuery.isFunction(layer_options)){\n            layer_options = layer_options(feature);\n        }\n        \n\n        if (!layer_options.pointToLayer) {\n            layer_options.pointToLayer = function (featureData, latlng) {\n                return new L.CircleMarker(latlng, { radius : 5 });\n            };\n        }\n    \n        this.layer = new L.GeoJSON(null, layer_options).addTo(map);\n\n        var overlayControl = {\n            \'Waypoints\' : this.layer\n        };\n\n        L.control.layers(null, overlayControl, {\n            collapsed : false\n        }).addTo(map);\n    },\n\n    // clear all geoJSON layers\n    clearLayer : function(){\n        for (var i in this.layer._layers) {\n            this.layer.removeLayer(this.layer._layers[i]);            \n        }\n    },\n\n    // add new geoJSON layer\n    addLayer : function(geoJSON) {\n        this.layer.addData(geoJSON);\n    }\n});\nL.Playback = L.Playback || {};\n\nL.Playback.DateControl = L.Control.extend({\n    options : {\n        position : \'bottomleft\',\n        dateFormatFn: L.Playback.Util.DateStr,\n        timeFormatFn: L.Playback.Util.TimeStr\n    },\n\n    initialize : function (playback, options) {\n        L.setOptions(this, options);\n        this.playback = playback;\n    },\n\n    onAdd : function (map) {\n        this._container = L.DomUtil.create(\'div\', \'leaflet-control-layers leaflet-control-layers-expanded\');\n\n        var self = this;\n        var playback = this.playback;\n        var time = playback.getTime();\n\n        var datetime = L.DomUtil.create(\'div\', \'datetimeControl\', this._container);\n\n        // date time\n        this._date = L.DomUtil.create(\'p\', \'\', datetime);\n        this._time = L.DomUtil.create(\'p\', \'\', datetime);\n\n        this._date.innerHTML = this.options.dateFormatFn(time);\n        this._time.innerHTML = this.options.timeFormatFn(time);\n\n        // setup callback\n        playback.addCallback(function (ms) {\n            self._date.innerHTML = self.options.dateFormatFn(ms);\n            self._time.innerHTML = self.options.timeFormatFn(ms);\n        });\n\n        return this._container;\n    }\n});\n    \nL.Playback.PlayControl = L.Control.extend({\n    options : {\n        position : \'bottomright\'\n    },\n\n    initialize : function (playback) {\n        this.playback = playback;\n    },\n\n    onAdd : function (map) {\n        this._container = L.DomUtil.create(\'div\', \'leaflet-control-layers leaflet-control-layers-expanded\');\n\n        var self = this;\n        var playback = this.playback;\n        playback.setSpeed(100);\n\n        var playControl = L.DomUtil.create(\'div\', \'playControl\', this._container);\n\n\n        this._button = L.DomUtil.create(\'button\', \'\', playControl);\n        this._button.innerHTML = \'Play\';\n\n\n        var stop = L.DomEvent.stopPropagation;\n\n        L.DomEvent\n        .on(this._button, \'click\', stop)\n        .on(this._button, \'mousedown\', stop)\n        .on(this._button, \'dblclick\', stop)\n        .on(this._button, \'click\', L.DomEvent.preventDefault)\n        .on(this._button, \'click\', play, this);\n        \n        function play(){\n            if (playback.isPlaying()) {\n                playback.stop();\n                self._button.innerHTML = \'Play\';\n            }\n            else {\n                playback.start();\n                self._button.innerHTML = \'Stop\';\n            }                \n        }\n\n        return this._container;\n    }\n});    \n    \nL.Playback.SliderControl = L.Control.extend({\n    options : {\n        position : \'bottomleft\'\n    },\n\n    initialize : function (playback) {\n        this.playback = playback;\n    },\n\n    onAdd : function (map) {\n        this._container = L.DomUtil.create(\'div\', \'leaflet-control-layers leaflet-control-layers-expanded\');\n\n        var self = this;\n        var playback = this.playback;\n\n        // slider\n        this._slider = L.DomUtil.create(\'input\', \'slider\', this._container);\n        this._slider.type = \'range\';\n        this._slider.min = playback.getStartTime();\n        this._slider.max = playback.getEndTime();\n        this._slider.value = playback.getTime();\n\n        var stop = L.DomEvent.stopPropagation;\n\n        L.DomEvent\n        .on(this._slider, \'click\', stop)\n        .on(this._slider, \'mousedown\', stop)\n        .on(this._slider, \'dblclick\', stop)\n        .on(this._slider, \'click\', L.DomEvent.preventDefault)\n        //.on(this._slider, \'mousemove\', L.DomEvent.preventDefault)\n        .on(this._slider, \'change\', onSliderChange, this)\n        .on(this._slider, \'mousemove\', onSliderChange, this);           \n\n\n        function onSliderChange(e) {\n            var val = Number(e.target.value);\n            playback.setCursor(val);\n        }\n\n        playback.addCallback(function (ms) {\n            self._slider.value = ms;\n        });\n        \n        \n        map.on(\'playback:add_tracks\', function() {\n            self._slider.min = playback.getStartTime();\n            self._slider.max = playback.getEndTime();\n            self._slider.value = playback.getTime();\n        });\n\n        return this._container;\n    }\n});      \n\nL.Playback = L.Playback.Clock.extend({\n        statics : {\n            MoveableMarker : L.Playback.MoveableMarker,\n            Track : L.Playback.Track,\n            TrackController : L.Playback.TrackController,\n            Clock : L.Playback.Clock,\n            Util : L.Playback.Util,\n\n            TracksLayer : L.Playback.TracksLayer,\n            PlayControl : L.Playback.PlayControl,\n            DateControl : L.Playback.DateControl,\n            SliderControl : L.Playback.SliderControl\n        },\n\n        options : {\n            tickLen: 250,\n            speed: 1,\n            maxInterpolationTime: 5*60*1000, // 5 minutes\n\n            tracksLayer : true,\n\n            playControl: false,\n            dateControl: false,\n            sliderControl: false,\n\n            // options\n            layer: {\n                // pointToLayer(featureData, latlng)\n            },\n\n            marker : {\n                // getPopup(feature)\n            }\n        },\n\n        initialize : function (map, geoJSON, callback, options) {\n            L.setOptions(this, options);\n\n            this._map = map;\n            this._trackController = new L.Playback.TrackController(map, null, this.options);\n            L.Playback.Clock.prototype.initialize.call(this, this._trackController, callback, this.options);\n\n            if (this.options.tracksLayer) {\n                this._tracksLayer = new L.Playback.TracksLayer(map, options);\n            }\n\n            this.setData(geoJSON);\n\n\n            if (this.options.playControl) {\n                this.playControl = new L.Playback.PlayControl(this);\n                this.playControl.addTo(map);\n            }\n\n            if (this.options.sliderControl) {\n                this.sliderControl = new L.Playback.SliderControl(this);\n                this.sliderControl.addTo(map);\n            }\n\n            if (this.options.dateControl) {\n                this.dateControl = new L.Playback.DateControl(this, options);\n                this.dateControl.addTo(map);\n            }\n\n        },\n\n        clearData : function(){\n            this._trackController.clearTracks();\n\n            if (this._tracksLayer) {\n                this._tracksLayer.clearLayer();\n            }\n        },\n\n        setData : function (geoJSON) {\n            this.clearData();\n\n            this.addData(geoJSON, this.getTime());\n\n            this.setCursor(this.getStartTime());\n        },\n\n        // bad implementation\n        addData : function (geoJSON, ms) {\n            // return if data not set\n            if (!geoJSON) {\n                return;\n            }\n\n            if (geoJSON instanceof Array) {\n              for (var i = 0, len = geoJSON.length; i < len; i++) {\n                this._trackController.addTrack(new L.Playback.Track(geoJSON[i], this.options), ms);\n              }\n            } else {\n              if (geoJSON.type == "FeatureCollection") {\n                for (var i = 0, len = geoJSON.features.length; i < len; i++) {\n                  this._trackController.addTrack(new L.Playback.Track(geoJSON.features[i], this.options), ms);\n                }\n              } else {\n                this._trackController.addTrack(new L.Playback.Track(geoJSON, this.options), ms);\n              }\n            }\n\n            this._map.fire(\'playback:set:data\');\n\n            if (this.options.tracksLayer) {\n                this._tracksLayer.addLayer(geoJSON);\n            }\n        },\n\n        destroy: function() {\n            this.clearData();\n            if (this.playControl) {\n                this._map.removeControl(this.playControl);\n            }\n            if (this.sliderControl) {\n                this._map.removeControl(this.sliderControl);\n            }\n            if (this.dateControl) {\n                this._map.removeControl(this.dateControl);\n            }\n        }\n    });\n\nL.Map.addInitHook(function () {\n    if (this.options.playback) {\n        this.playback = new L.Playback(this);\n    }\n});\n\nL.playback = function (map, geoJSON, callback, options) {\n    return new L.Playback(map, geoJSON, callback, options);\n};\n\nreturn L.Playback;\n\n}));\n'

fname_embedded_code = os.path.join(path_outputs,'LeafletPlayBack.js')
if not os.path.exists(fname_embedded_code):
    with open(fname_embedded_code,'w', encoding='utf-8') as fout:
        fout.write(LeafletPlayBack_js)

example_labdrones_html = """<!DOCTYPE html>
<html>

<head>
    <title>LabDrones Geotagging Tool</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Leaflet 0.7.7 CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@0.7.7/dist/leaflet.css" />

    <!-- Bootstrap 2.3.2 CSS -->
    <link rel="stylesheet" href="https://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-combined.min.css" />

    <!-- jQuery UI CSS -->
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />

    <!-- Font Awesome & Awesome Markers CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.1.0/css/font-awesome.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.0/leaflet.awesome-markers.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-timepicker/0.5.2/css/bootstrap-timepicker.min.css" />

    <!-- Application-specific CSS -->
    <link rel="stylesheet" href="example_2.css" type="text/css" />

    <style>
    #title_container {
        z-index: 10000;
        position: fixed;
        left: 100px;
        color: white;
    }

    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
    }

    #map {
        width: 100vw;
        height: 100vh;
    }

    h1 {
        font-size: 36px;
        font-weight: 300;
        line-height: 1.1;
    }

    .datetimeControl p {
        margin: 0;
        font-size: 16px;
    }
    </style>
</head>

<body>
    <div id="title_container"></div>

    <!-- Main map container -->
    <div id="map"></div>

    <!-- Library Scripts (Strict Order) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js"></script>
    <script src="https://unpkg.com/leaflet@0.7.7/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/2.3.2/js/bootstrap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-timepicker/0.5.2/js/bootstrap-timepicker.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.0/leaflet.awesome-markers.js"></script>

    <!-- Project Local Scripts -->
    <script src="LeafletPlayBack.js"></script>
    <script src="labdrones_tracks.js"></script>
    <script src="example_2_control.js"></script>
    <script src="example_labdrones.js"></script>
</body>
</html>"""


# --------------------------
#        Functions
# --------------------------

def open_html_in_browser(file_path):
    """
    Opens the HTML file in the default browser.
    """
    abs_path = os.path.abspath(file_path)

    try:
        return webbrowser.open(f"file://{abs_path}")
    except Exception:
        return False


def open_window_about():
    # Tab 1: Third-Party Licenses
    tab_licenses = [
        [sg.Text("Third-Party Open Source Components:", font=("Helvetica", 11, "bold"))],
        [sg.Multiline(LEAFLET_PLAYBACK_LICENSE, disabled=True, font=multiline_text_font, expand_x=True, expand_y=True, autoscroll=True)]
    ]

    # Tab 2: Acknowledgments and Funding
    tab_ack = [
        [sg.Text("Funding & Support", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(WELLCOME_NOTICE, disabled=True, font=("Helvetica", 11), expand_x=True, expand_y=True)]
    ]

    # General Layout
    layout_sobre = [
        [sg.Text("LabDrones Geotagging Tool", font=("Helvetica", 14, "bold"), pad=((10, 10), (15, 5)))],
        [
            sg.TabGroup(
                [[
                    sg.Tab("Third-Party Licenses", tab_licenses),
                    sg.Tab("Acknowledgments", tab_ack)
                ]],
                expand_x=True,
                expand_y=True,
                pad=(10, 10)
            )
        ],
        [
            sg.Push(),
            sg.Button("Close", key="-CLOSE_ABOUT-", size=(10, 1)),
            sg.Push()
        ]
    ]

    window_about = sg.Window(
        "About, Licenses and Acknowledgments",
        layout_sobre,
        size=(modal_width, modal_height),
        resizable=True, 
        keep_on_top=True,
        finalize=True
    )

    try:
        # Links to the main window so that Linux understands the correct window stacking order
        window_about.TKroot.transient(window.TKroot) 
        # Forces immediate rendering without waiting for mouse movement
        window_about.TKroot.update() 
    except Exception as e:
        pass

    while True:
        event, _ = window_about.read()
        if event in (sg.WINDOW_CLOSED, "-CLOSE_ABOUT-"):
            break

    window_about.close()


def _rm_file(filename):
    try:
        with suppress(FileNotFoundError):
            os.remove(filename)
    except OSError as err:
       print(err)
         

def popup(message, progress_bar=0):
    sg.theme('DarkGrey')    
    layout = [[sg.Text(message)]]
    if progress_bar:
        layout = [[sg.Text(message)],
                  [sg.ProgressBar(progress_bar, orientation="h", size=(58, 5), key='progress', border_width=4, bar_color=("Blue","Yellow"))],
                  [sg.Text('', key='-OUT-', enable_events=True, font=('Arial Bold', 16), justification='center', expand_x=True)],
                  [sg.Cancel()]
                  ]
    window_popup = sg.Window('', layout, no_titlebar=True, keep_on_top=True, finalize=True)
    return window_popup


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + (float(coords[1]) / 60) + (float(coords[2]) / 3600)
    if ref == "S" or ref == "W":
        decimal_degrees = -decimal_degrees
    return decimal_degrees


# Features - https://www.dji.com/br/phantom-3-adv
# The sensor is 6.16mm wide and 4.62mm high. The maximum created still image size is 4000 pixels wide by 3000 tall - https://forum.dji.com/forum.php?mod=redirect&goto=findpost&ptid=28597&pid=197705
# Pixel size at sensor (Square): 1.562 micrometer
# Sensor size at X (TSX): 6.248 mm
# Sensor size at Y (TSY): 4.686 mm

# Features - https://sdk-forum.dji.net/hc/en-us/articles/12325496609689-What-is-the-custom-camera-parameters-for-Mavic-3-Enterprise-series-and-Mavic-3M
# The device have 4 cameras (RGB) and Multispectral (G, Red, Red Edge and Near Infrared)
# Image size	5280x3956 (RGB)	2592x1944 (MS)
# Sensor size at X (TSX): 17.4mm (RGB) 5.2mm (MS)
# Sensor size at Y (TSY): 13mm (RGB) 3.9mm (MS)

# Features - https://enterprise.dji.com/mavic-3-enterprise/specs
# The Mavic 3T's thermal camera offers a 640 × 512 resolution and supports features like point and area temperature measurement, high-temperature alerts, customizable color palettes, and isotherms - 
# Thermal Camera Uncooled VOx Microbolometer
# Pixel size at sensor (Pixel Pitch): 12 micrometer
# Equivalent Focal Length 40mm
# Infrared Wavelength 8-14 μm
# Temperature Measurement Range:
# -20° to 150° C (-4° to 302° F, High Gain Mode)
#   0° to 500° C (32° to 932° F, Low Gain Mode)

def get_exif_info(img_path):
    img = Image.open(img_path)
    if img._getexif() != None:
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
       
        try:
            coordenadas = exif['GPSInfo']
            altitude =  coordenadas[6]
            lat = decimal_coords(coordenadas[2], coordenadas[1])
            lon = decimal_coords(coordenadas[4], coordenadas[3])
            
        except KeyError:
            print('No Coordinates')            
    else:
        print('The image has no EXIF information:\n'+img_path)
        return None

    return {'focal_lenght':float(exif['FocalLength']),'date':str(exif['DateTime']),'img_dim_x':int(exif['ExifImageWidth']),'img_dim_y':int(exif['ExifImageHeight']),'center_coords':(float(lat),float(lon)),'altitude':float(altitude)}


def write_track(nr,df_tmp, file_out):    
    title = df_tmp.mission.iloc[0] + \
    ' Starts:' + df_tmp.loc[0,['Date Shot']].values[0].split()[1] 
    
    df_tmp['coordinates'] = df_tmp[['lon_deg', 'lat_deg']].apply(list, axis=1)
    
    w_js = 'var track'+str(nr)+' = { \n\
      "type": "Feature", \n\
      "geometry": { \n\
      "type": "MultiPoint", \n\
      "coordinates": ' +  df_tmp['coordinates'].to_json(orient='records', indent=8) + \
      '}, \n\
      "properties": { \n\
        "title" : "' + title + '", \n\
        "path_options" : { "color" : "'+ names_color[nr] + '" }, \n\
        "images": ' + df_tmp['File'].to_json(orient='records', indent=10) + \
       ', \n\
        "time": ' + df_tmp['unix-timestamp'].to_json(orient='records', indent=10) + \
       ', \n\
        "altitude": ' + df_tmp['Altitude'].to_json(orient='records', indent=10) + \
      '\n}, \n};\n'
    
    with open(file_out, 'a', encoding='utf-8') as f:
        print(w_js, file=f)
    

def process_flights(flights_path):
    flights_path = sorted(flights_path)
    overview_key = '-'.join([os.path.basename(str(path)) for path in flights_path])

    if overview_key in overviews_info:
        html_file_path = overviews_info[overview_key]
    
        # Try opening the HTML file in the browser (supports WSL, Windows, and Linux)
        opened = open_html_in_browser(html_file_path)
        
        if opened:
            sg.popup_quick_message(
                "The application has been successfully launched in your default browser!",
                title="Information",
                keep_on_top=True,
                background_color='#16a085',
                text_color='white',
                font=("Helvetica", 11, "bold")
            )
        else:
            # Fallback if it is not possible to open the browser automatically
            sg.popup_ok(
                f"The result file with image overview was saved at:\n\n{html_file_path}\n\n"
                "Please open it manually in your web browser.",
                title="Information",
                keep_on_top=True
            )
    else:
        fid, target_file = tempfile.mkstemp(suffix='.js', prefix='labdrones_tracks_')
        popup_win = popup('Processing flights scenes, please wait...', progress_bar=len(flights_path))
        popup_win.refresh()
        popup_win.force_focus()
        progress_bar = popup_win['progress']
        t_elem = float(len(flights_path))

        all_flights_data = []
        all_lats = []
        all_lons = []

        # 1. Coleta e processa os dados de cada pasta independentemente
        for i, path in enumerate(flights_path):
            appended_data = []
            for file in Path(path).rglob('*.JPG'):
                exif_info = get_exif_info(file)
                
                # Calcula o unix timestamp
                unix_timestamp = int(datetime.datetime.timestamp(datetime.datetime.strptime(exif_info['date'], "%Y:%m:%d %H:%M:%S")) * 1000)
                
                lat_val = exif_info['center_coords'][0]
                lon_val = exif_info['center_coords'][1]

                appended_data.append([
                    str(file), exif_info['date'], lat_val, 
                    lon_val, exif_info['altitude'], unix_timestamp
                ])
                
                # Coleta global para o bounding box
                all_lats.append(lat_val)
                all_lons.append(lon_val)

            if not appended_data:
                progress_bar.update_bar(i + 1)
                continue

            mission = os.path.basename(os.path.normpath(path)) + '_' + appended_data[0][1].split()[0].replace(':', '-')
                        
            df = pd.DataFrame(appended_data, columns=['File', 'Date Shot', 'lat_deg', 'lon_deg', 'Altitude', 'unix-timestamp'])
            df['mission'] = mission
            df = df.sort_values(by=['unix-timestamp'])            
            
            # Armazena o dataframe e o tempo inicial para ordenação global
            all_flights_data.append({
                'start_time': df['unix-timestamp'].min(),
                'df': df
            })

            progress_bar.update_bar(i + 1)
            event, values = popup_win.read(timeout=0)
            if event == 'Cancel' or event == None:
                break

        popup_win.close()
        
        if event != 'Cancel' and event != None:
            # 2. ORDENAÇÃO GLOBAL: Ordena os voos cronologicamente pelo tempo de início
            all_flights_data = sorted(all_flights_data, key=lambda x: x['start_time'])

            tracks = []
            
            # Abre o arquivo para começar a escrever as tracks ordenadas individualmente via write_track
            # (Certifique-se de que a função write_track escreve no target_file sequencialmente com os nomes track0, track1...)
            for new_idx, flight_item in enumerate(all_flights_data):
                track_name = 'track' + str(new_idx)
                tracks.append(track_name)
                df_sorted = flight_item['df']
                write_track(new_idx, df_sorted, target_file)

            # 3. Cálculo do Bounding Box geral e do centro matemático no Python
            min_lat, max_lat = min(all_lats), max(all_lats)
            min_lng, max_lng = min(all_lons), max(all_lons)
            
            center_lat = (min_lat + max_lat) / 2
            center_lng = (min_lng + max_lng) / 2

            # 4. Escreve o rodapé do arquivo JavaScript com as variáveis globais
            w_js = f"""
var center_map = [{center_lat}, {center_lng}];
var zoom_level = 14;

var precalculatedBounds = [
    [{min_lat}, {min_lng}],
    [{max_lat}, {max_lng}]
];

var labdronesTracks = [{', '.join(tracks)}];
"""
            
            with open(target_file, 'a', encoding='utf-8') as f:
                print(w_js, file=f)

            # Store Javascript file and HTML needed to perform overview using Leaflet plugin and display the application in the default web browser:
            shutil.copy2(target_file,os.path.join(path_outputs,os.path.basename(target_file)))            
            fid_html, html_file = tempfile.mkstemp(suffix='.html', prefix='example_labdrones_')
            with open(html_file,'w', encoding='utf-8') as fname_html:
                fname_html.write(example_labdrones_html.replace('labdrones_tracks.js',os.path.basename(target_file)))
            shutil.copy2(html_file,os.path.join(path_outputs,os.path.basename(html_file)))

            overviews_info[overview_key] = os.path.join(path_outputs,os.path.basename(html_file))
            with open(fname_json, 'w', encoding='utf-8') as outfile:
                outfile.write(json.dumps(overviews_info, indent=4))
           
            # Full path to the generated file
            full_html_path = os.path.abspath(os.path.join(path_outputs, os.path.basename(html_file)))

            # Try opening the browser (it works on WSL, Linux, and Windows)
            opened_successfully = open_html_in_browser(full_html_path)

            if opened_successfully:
                sg.popup_quick_message(
                    "Map opened in your default browser!", 
                    title="Success", 
                    background_color='#16a085', 
                    text_color='white',
                    font=("Helvetica", 11, "bold")
                )
            else:
                # If it fails or if the user is in an environment without a browser
                layout_info = [
                    [sg.Text("Geotagging Completed Successfully!", font=("Helvetica", 11, "bold"))],
                    [sg.Text("The output file was saved at:")],
                    [sg.In(full_html_path, key="-PATH-", readonly=True, expand_x=True)],
                    [
                        sg.Button("Open Map in Browser", key="-OPEN-"),
                        sg.Button("Copy Path", key="-COPY-"),
                        sg.Button("OK", key="-OK-")
                    ]
                ]
                
                win_info = sg.Window("Process Completed", layout_info, modal=True, finalize=True)
                
                while True:
                    event, _ = win_info.read()
                    if event in (sg.WINDOW_CLOSED, "-OK-"):
                        break
                    elif event == "-OPEN-":
                        open_html_in_browser(full_html_path)
                    elif event == "-COPY-":
                        sg.clipboard_set(full_html_path)
                        sg.popup_quick_message("Path copied to clipboard!", background_color='#16a085', text_color='white')
                        
                win_info.close()
                        
                # Include temporary files to remove after the end:
                fname_temp_file_list = os.path.join(os.path.join(os.getcwd(),'geotagger_app-files-out'),'temp_files_list.txt')
                f = open(fname_temp_file_list, 'w', encoding='utf-8')
                print(target_file, file=f)
                print(html_file, file=f)
                f. close()
        

# --------------------------
#          Main
# --------------------------
# Remove temporary files created previously:
fname_temp_file_list = os.path.join(os.path.join(os.getcwd(),'geotagger_app-files-out'),'temp_files_list.txt')
if os.path.exists(fname_temp_file_list):
    with open(fname_temp_file_list) as f:
        for file in [line.rstrip() for line in f]:
            _rm_file(file)

# 1. Top Menu structure definition
# Format: [ "Menu Name", ["Option 1", "Option 2", "::Shortcut"] ]
menu_def = [
    ['&Exit', ['E&xit']],
    ['&Help', ['&About / Licenses']]
]

# 2. Definition of the Main Layout
layout = [[sg.Menu(menu_def, key='-MENU-', font=("Helvetica", 12, "bold"))],
    
    # Folder selection
    [
        sg.Frame('Choose the folder:', [
            [
                sg.In(enable_events=True, key="-FOLDER-", expand_x=True, expand_y=True),
                sg.FolderBrowse()
            ]
        ], pad=(0, 0), expand_x=True, expand_y=False)
    ],
    
    # Flights list
    [
        sg.Frame('Flights list:', [
            [
                sg.Listbox(
                    values=[], 
                    enable_events=True, 
                    size=(40, 20), 
                    key="-FILE LIST-", 
                    expand_x=True, 
                    expand_y=True
                )
            ]
        ], pad=(0, 0), expand_x=True, expand_y=True)
    ]
]

# --------------------------------- Create Window ---------------------------------
window = sg.Window(title_name, layout, finalize=True, size=(width,height), location=(0,0),
                   right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, keep_on_top=True, use_custom_titlebar=use_custom_titlebar,
                   enable_close_attempted_event=True, grab_anywhere=True)


# Increases the global scale of the interface and native windows (FolderBrowse/FileDialog)
# Values ​​between 1.5 and 2.0 work very well for high-resolution screens
window.TKroot.tk.call('tk', 'scaling', 2.0)


# --------------------------------- Event Loop ---------------------------------
while True:    
    event, values = window.read()
    if event in ("Exit","-WINDOW CLOSE ATTEMPTED-", 'E&xit'):
        break

    # Event to open the About/Licenses window
    if event in ('About / Licenses', '&About / Licenses', '-ABOUT-'):
        open_window_about()

    # Folder name was filled in, make a list of files in the folder
    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        try:            
            file_list =  list(set([str(path.parent.parent) for path in Path(folder).rglob('*.JPG')]))
        except:
            file_list = []

        if len(file_list) > 0:
            window["-FILE LIST-"].update(file_list)
            try:
                window["-FILE LIST-"].Widget.configure(fg="black")
            except:
                pass
            window.refresh()            
            process_flights(file_list)
        else:
            empty_msg = ["No flight containing .JPG files was found in the selected folder!"]
            window["-FILE LIST-"].update(empty_msg)
            try:
                window["-FILE LIST-"].Widget.configure(fg="#d32f2f")
            except:
                pass
            window.refresh()            

# --------------------------------- Close & Exit ---------------------------------
window.close()