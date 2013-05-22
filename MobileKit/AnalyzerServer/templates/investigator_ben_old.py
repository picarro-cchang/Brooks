.analysisIcon
{
  backgroundColor:rgb(255,96,96);
  borderStyle:solid;
  borderWidth:2px;
  padding:2px;
  font-family:Arial;
  font-size:16;
}
img.follow
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -4px 0px;
}
img.follow-checked
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -60px 0px;
}
img.overlay
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -116px -1px;
}
img.overlay-checked
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -170px -1px;
}
img.wifi-0
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -224px -1px;
}
img.wifi-1
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -280px -1px;
}
img.wifi-2
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -336px -2px;
}
img.wifi-3
{
width:48px;
height:48px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -390px -2px;
}
img.stream-ok
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -448px -4px;
}
img.stream-warning
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -496px -4px;
}
img.stream-failed
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -545px -5px;
}
img.analyzer-ok
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -592px -4px;
}
img.analyzer-failed
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -638px -4px;
}
img.gps-ok
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -683px -4px;
}
img.gps-failed
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -733px -4px;
}
img.gps-uninstalled
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -783px -4px;
}
img.gps-warning
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -983px -4px;
}
img.ws-ok
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -832px -5px;
}
img.ws-failed
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -883px -5px;
}
img.ws-uninstalled
{
width:40px;
height:40px;
background:url("{{ url_for('static',filename='images/icons/icon-combined-all-v5.png') }}") -933px -5px;
}
    <div class="container-fluid" style="height:800px; width:700px;">
        <!--
        <audio id="plume">
           <source src="/static/sound/beep-7.mp3" />
           <source src="/static/sound/beep-7.wav" />
        </audio>
        -->
        <div class="span3" id="id_sidebar" data-no-collapse="true" style="margin-left:0;">
            <div class="sidebar-nav">
                <!-- <div class="navbar navbar-fixed-top" style="height: 45px;" id="id_topleft">
                   <div class="navbar-left-inner" style="height: 45px;" id="id_topleftbar">
                       <div id="id_p3_icon">
                        <img alt="Picarro" src="/static/images/pcube_ppp_logo_60.png" height="40" />
                       </div>
                   </div>
                </div><br /><br /><br />
                <div style="height: 45px;" id="id_sidebar_spacer"></div>
 -->
                <span>
                    <form id="setoptions" method="get">

                    <div id="id_side_modal_span">
                      <div id="id_smsg"></div>
                      <div id="id_smodal"></div>
                      <div id="id_smod_change"></div>
                    </div>
                    <div id="id_modal_span">
                      <div id="id_msg"></div>
                      <div id="id_modal"></div>
                      <div id="id_weather" class="modal fade hide"></div>
                      <div id="id_mod_change"></div>
                    </div>

                        <br />

                        <fieldset>
                          <div class="clearfix">
                            <ul class="unstyled">
                            <div style="margin-left:2px; height:25px;" id="placeholder"><img alt="Initializing Route Trace" src="/static/images/ajax-loader.gif" /></div>
                            <div style="margin-left:2px; margin-top:10px; margin-bottom:10px;" id="concAndWind">
                                <span style="margin-right:28px;" id="concData"></span>
                                <span id="windData"></span>
                            </div>
                                <!-- <span id="concentrationSparkline"></span> -->
                                  <span id="windRose">
                                      <canvas id="windCanvas" width="50" height="50"/>
                                  </span>
                                <li>
<!--                                     <div id="id_statusPane"></div>
                                    <div id="id_followPane"></div>
                                    <div id="id_modePane"></div>
                                    <div id="id_primeControlButton_span"></div> -->
                                    <span id="id_exportButton_span"></span>                                    
                                    <span class='btn' id='tmp_insert_btn'>insert</span>
                                    <span class='btn' id='tmp_clear_btn'>clear</span>
                                    <span class='btn' id='tmp_stats_btn'>stats</span>
                                    <span class='btn' id='tmp_wind_btn'>wind</span>
                                   <!--  <br/>
                                    <select id='color_select'>
                                      <option value="YlGn">YlGn</option>
                                      <option value="YlGnBu">YlGnBu</option>
                                      <option value="GnBu">GnBu</option>
                                      <option value="BuGn">BuGn</option>
                                      <option value="PuBuGn">PuBuGn</option>
                                      <option value="PuBu">PuBu</option>
                                      <option value="BuPu">BuPu</option>
                                      <option value="RdPu">RdPu</option>
                                      <option value="PuRd">PuRd</option>
                                      <option value="OrRd">OrRd</option>
                                      <option value="YlOrRd">YlOrRd</option>
                                      <option value="YlOrBr">YlOrBr</option>
                                      <option value="Purples">Purples</option>
                                      <option value="Blues" selected>Blues</option>
                                      <option value="Greens">Greens</option>
                                      <option value="Oranges">Oranges</option>
                                      <option value="Reds">Reds</option>
                                      <option value="Greys">Greys</option>
                                    </select> -->
                                    <br/>
                                    <!-- <span id='color-picker'></span> -->
                                    <span id="tmp_queue_len"></span>

                                </li>
                                <li>
                                      <!-- <input style="width: 100%;" type="submit" name="F3967418176244ND1N5" class="btn btn-primary btn-fullwidth" value="Select Surveyor" /> -->
                                </li>
                            </ul>
                          </div>
                        </fieldset>
                    </form>
                </span>

            </div>
        </div>

        <div class="span9" id="id_content">
            <!-- <span>

            <div class="navbar navbar-fixed-top" id="id_topright">
                    <div class="navbar-inner" id="id_topbar">
                          <div class="container">
                            <div id='time_slider' class='generic_slider'></div>
                            
                            <ul class="nav nav-pills pull-left">

                            </ul>

                        </div>
                    </div>
            </div>
            </span> -->
            <script type="text/javascript">$('.dropdown-toggle').dropdown()</script>

            <div id="id_content_spacer" style="height: 45px;"></div>
            <div class="row">
                <div class="span4" id="id_content_title">
                    <h2>Picarro Investigator&#8482;</h2>
                </div>
                <div class="span5" id="id_legend_div">
                    <div id="id_legend_canvas" width="1000" height="50">
                    </div>
                </div>
            </div>
            <span>
              <div class="row">
                <div class="span9">
                    <div id="id_feedback">
                      <div style="float:left;" id="id_msg_placeholder">
                      </div>
                      <div style="float:left;">      </div>
                      <div style="float:left;" id="concData"></div>
                      <div style="float:left;">      </div>
                      <div style="float:left;" id="counter"></div>
                    </div>
                    <br />
                    <!-- <div style="height:100%; top: 5px; bottom: 5px;" id="map_canvas"></div> -->
                    <div style="height:100%; top: 5px; bottom: 5px; display:none;" id="map2_canvas"></div>
                    <div id="map2_flot"></div>
                    <div id="map2_histo"></div>
                    <div id='range_slider' class='generic_slider'></div>
                </div>
                <div class="span9" id="id_below_map">
                    
                </div>
              </div>
            </span>
        </div>

    </div>
    </div>