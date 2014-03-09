/*************************************************************************** 
* This file is part of the Frescobaldi project, http://www.frescobaldi.org/
*
* Copyright (c) 2008 - 2012 by Wilbert Berendsen
*
* This program is free software; you can redistribute it and/or
* modify it under the terms of the GNU General Public License
* as published by the Free Software Foundation; either version 2
* of the License, or (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program; if not, write to the Free Software
* Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
* See http://www.gnu.org/licenses/ for more information.
*/
window.addEventListener('error', error, false); 

var last_m, drag = null;
var svgarr = document.getElementsByTagName("svg");
var svg = svgarr[0];
var maxX = svg.offsetWidth-1;
var maxY = svg.offsetHeight-1;
var txt = document.getElementsByTagName('text');

//remove this
onmouseup = function(){ 
	drag = null;
	pyLinks.pyLog("drag stopped externally!");
	 
};

//listen for drag events on all text elements
//and get their initial position
for (var t= 0; t < txt.length; ++t){

	txt[t].onmousedown = txt[t].onmousemove = txt[t].onmouseup = Drag;	
	
}

//write error message
function error(e){
	pyLinks.pyLog(e.message);
}

//moving objects with mouse
function Drag(e){
	
	//pyLinks.pyLog('drag activated by '+this+e.type);			
	
	e.stopPropagation();
	var ct = e.target, et = e.type, m = mousePos(e);
	
	var tr = this.transform.baseVal.getItem(0);
	if (tr.type == SVGTransform.SVG_TRANSFORM_TRANSLATE){
		var e = tr.matrix.e, f = tr.matrix.f;
	}

	//start drag
	if (!drag && (et == "mousedown")){
		//pyLinks.pyLog('dragging started');
		drag = ct;
		last_m = m;	
		
		x = mm2pix(e);
		y = mm2pix(f);
		
		//pyLinks.pyLog(x+':'+y);		
	}
	
	//drag
	if (drag && (et == "mousemove")){
		//pyLinks.pyLog('dragging ongoing');
		x += m.x - last_m.x;
		y += m.y - last_m.y;
		last_m = m;	
		tr.setTranslate(pix2mm(x),pix2mm(y));
		
		//pyLinks.pyLog(m.x+':'+m.y);
		//pyLinks.pyLog(x+':'+y);
		
	}
	
	//stop drag
	if (drag && (et == "mouseup")){
		drag = null;
		//pyLinks.pyLog('dragging stopped');	
	}

}

//mouse position
function mousePos(event) {
	return {
		x: Math.max(0, Math.min(maxX, event.pageX)),
		y: Math.max(0, Math.min(maxY, event.pageY))
	}
}

//we need to convert between pixels and millimeters
function pix2mm(pixval){
	return (pixval*25.4)/96;
}
function mm2pix(mmval){
	return (mmval*96)/25.4;
}
	
function getSVG(){
	
	if (typeof(XMLSerializer) !== 'undefined') {
		var serializer = new XMLSerializer();
		pyLinks.saveSVG(serializer.serializeToString(svg));
   }	
}

