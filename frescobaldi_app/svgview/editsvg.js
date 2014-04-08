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
	 
};

//listen for drag events on all text elements
//and save their initial position
for (var t= 0; t < txt.length; ++t){

	txt[t].onmousedown = txt[t].onmousemove = txt[t].onmouseup = Drag;
	
	var doSave = pyLinks.savePos();
	
	if (doSave){
		var p = getTranslPos(txt[t]);	
		txt[t].setAttribute("init-x",p.x);
		txt[t].setAttribute("init-y",p.y);
	}
}

pyLinks.setSaved();

//write error message
function error(e){
	pyLinks.pyLog(e.message);
}

//moving objects with mouse
function Drag(e){		
	
	e.stopPropagation();
	var ct = e.target, et = e.type, m = mousePos(e);
	
	var tp = getTranslPos(this);
	var tr = tp.tr;

	//drag start
	if (!drag && (et == "mousedown")){
		
		drag = ct;
		last_m = m;	
		
		x = tp.x;
		y = tp.y;
				
	}
	
	//drag
	if ((drag == ct)  && (et == "mousemove")){
		
		//change color when element has been changed
		this.setAttribute("fill", "orange");
		
		x += m.x - last_m.x;
		y += m.y - last_m.y;
		last_m = m;	
		tr.setTranslate(x,y);
		
	}
	
	//dragging stopped
	if (drag && (et == "mouseup")){
		drag = null;
		//pyLinks.pyLog("x="+x+":y="+y);
		
		var initX = parseFloat(this.getAttribute("init-x"));
		var initY = parseFloat(this.getAttribute("init-y"));
		
		//pyLinks.pyLog("init x="+initX+":init y="+initY);
		
		var diffX = getDiffPos(x, initX);
		var diffY = getDiffPos(y, initY);
		
		pyLinks.calcOffset(diffX, diffY);
		
		//adjust to rounded diff
		var newX = initX - diffX;
		var newY = initY - diffY;
		
		//pyLinks.pyLog("new x="+newX+":new y="+newY);
		
		tr.setTranslate(newX,newY);	
	}

}

//mouse position
function mousePos(event) {
	var svgPoint = svg.createSVGPoint();

    svgPoint.x = event.clientX;
    svgPoint.y = event.clientY;

    svgPoint = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
    
    return svgPoint;
}

//get markup translate coordinates
function getTranslPos(elem){
	var tr = elem.transform.baseVal.getItem(0);
	if (tr.type == SVGTransform.SVG_TRANSFORM_TRANSLATE){
		return { 
			x: tr.matrix.e, y: tr.matrix.f, tr: tr
		}
	}
}

//return difference between initial and current position
function getDiffPos(p, initP){
	
	return roundPos(initP - p);
}

//round position to two decimals	
function roundPos(pos){
	return Math.round(pos * 100) / 100;
}
	
function getSVG(){
	
	if (typeof(XMLSerializer) !== 'undefined') {
		var serializer = new XMLSerializer();
		pyLinks.saveSVG(serializer.serializeToString(svg));
   }	
}

