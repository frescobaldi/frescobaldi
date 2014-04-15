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

var svgarr = document.getElementsByTagName("svg");
var svg = svgarr[0];
var maxX = svg.offsetWidth-1;
var maxY = svg.offsetHeight-1;
var draggable = document.getElementsByTagName('a');
var draggedObject = null;

var clone, delNode;

//listen for drag events on all text elements
//and save their initial position
for (var t= 0; t < draggable.length; ++t){
	
	//transform attribute can be in link element itself
	if(draggable[t].hasAttribute("transform")){
		enableTranslPositioning(draggable[t])
	}
	 
	var node = draggable[t].firstChild;
	
	var childs = new Array();
	
	//loop through the children of every draggable node
	while(node){		
		// so far only enable dragging of 
		// nodes with the transform attribute
		if(node.nodeType==1 && node.hasAttribute("transform")){
			
			childs.push(node);
			
			enableTranslPositioning(node)
					
		}
		node = node.nextSibling;
	}
	//group elements together if the belong to the same link tag
	if(childs.length>1){
		draggable[t].group = childs;
	}
}

pyLinks.setSaved();

//I'm putting this back in at least for now
//generic onmouseup
//needed when dragging doesn't keep mouse over object
onmouseup = function(e){ 
	MouseUp(e);	 
};

//write error message
function error(e){
	pyLinks.pyLog(e.message);
}

function enableTranslPositioning(node){
	enableMouseEvents(node);
			
	var doSave = pyLinks.savePos();

	if (doSave){
		var p = getTranslPos(node);	
		node.setAttribute("init-x",p.x);
		node.setAttribute("init-y",p.y);
	}
}	

function enableMouseEvents(elem){
	elem.onmousedown = MouseDown;
	elem.onmousemove = MouseMove;
	elem.onmouseup = MouseUp;
}

function Point(x, y){
  this.x = x;
  this.y = y;

  function distanceTo(otherPoint){
    distX = getRoundDiffPos(otherPoint.x, this.x);
    distY = getRoundDiffPos(otherPoint.y, this.y);
    return Point(distX, distY);
  };
}

function DraggableObject(e){
  pyLinks.pyLog("Create DraggableObject");
  this.target = e.target;
  var mouse = mousePos(e);

  // Reference point for dragging operation
  this.startDrag = new Point(mouse.x, mouse.y);

  // load original (LilyPond's) position of the object
	var initX = parseFloat(this.target.getAttribute("init-x"));
	var initY = parseFloat(this.target.getAttribute("init-y"));
  this.initPos = new Point(initX, initY);

  // determine the current position at the start of a (new) drag
  var tmpStartPos = getTranslPos(this.target);
  this.transform = startPos.tr;
  //catch type of element by sending link
    
  this.startPos = new Point(tmpStartPos.x, tmpStartPos.y);

  pyLinks.pyLog(this.startPos.x.toString());
  
//  this.startDrag = startDrag;
  
  this.startOffset = function(){
    return this.initPos.distanceTo(this.startPos)
  };
}

var draggedObject = null;

function calcPositions(e){
    // calculate all the necessary values while dragging
    // these should better be properties of an object
    // because many of them don't have to be stored as values.
    dragPos = mousePos(e);
    // current offset of the dragging operation itself
    dragOffX = getRoundDiffPos(dragPos.x, dragOrigin.x);
    dragOffY = getRoundDiffPos(dragPos.y, dragOrigin.y);
    // current position of the object
    currX = startX + dragOffX;
    currY = startY + dragOffY;
    // current offset of the object against its init position
    currOffX = startOffX + dragOffX;
    currOffY = startOffY - dragOffY;
}

function MouseDown(e){
  e.stopPropagation();
  draggedObject = new DraggableObject(e);
    // Set flags and values for the drag operation
  pyLinks.pyLog("DraggableObject was created");
    
//  var mouse = mousePos(e);
//  var startDrag = new Point(mouse.x, mouse.y);

  // load original (LilyPond's) position of the object
//	var initX = parseFloat(this.getAttribute("init-x"));
//	var initY = parseFloat(this.getAttribute("init-y"));
//  var initPos = new Point(initX, initY);
  
  
  //catch type of element by sending link
  pyLinks.dragElement(this.parentNode.getAttribute('xlink:href'))

  // announce original position (may already have an offset)
  pyLinks.startDragging(startOffX, startOffY);
//  var startPos = getTranslPos(this);
//  objTransform = startPos.tr;
  //catch type of element by sending link
  pyLinks.dragElement(this.parentNode.getAttribute('xlink:href'))
    
//  startPos = new Point(startPos.x, startPos.y);
  //catch type of element
      
  
  //ensure that the selected element will always be on top by putting it last in the node list
  //Clone the node to make sure we can put it back when drag is finished
  clone = this.cloneNode(true);
  //keep reference to parent
  this.parent = this.parentNode;
  this.parentNode.replaceChild(clone, this);
  svg.appendChild(this);
  
  //prepare deletion
  delNode = this;
  
  //make the clone transparent
  //This can be set to 0 to preserve previous behaviour,
  //but I think this has a nice touch.
  clone.setAttribute("opacity", "0.3");  

// announce original position (may already have an offset)
  pyLinks.startDragging(draggedObject.startOffset());

}

function MouseMove(e){
  e.stopPropagation();
  // ignore events from other objects than the dragged one
  // This doesn't work reliably yet. When an object is dragged
  // _under_ another one the event is only triggered for the wrong one.
  if (e.target == draggedObject){
    // calculate mouse coordinates relative to the drag's starting position
//    calcPositions(e);
    
    // move the object to the new position
    if(this.parent.group){
		// move whole group together
		// to-do: calculate position for each element in the group
		setGroupTranslate(this.parent.group, currX, currY); 
	}else{
		objTransform.setTranslate(currX, currY);
	}
      
    // announce the new position
    pyLinks.dragging(currOffX, currOffY);
  }
}

function MouseUp(e){
	
	//set the new position for the clone
	var clonePos = getTranslPos(clone);
	cloneTransform = clonePos.tr;
	cloneTransform.setTranslate(currX, currY);
	
	//remove transparency
	clone.removeAttribute("opacity");
  
	//change color when object is modified
    if(clone.getAttribute("fill") != "orange"){
		clone.setAttribute("fill", "orange");
	}
	
	//enable further editing
	enableMouseEvents(clone);
        
    // calculate positions, is only necessary for the signal
    calcPositions(e);
    pyLinks.dragged(currOffX, currOffY);
        
    // clean up
    draggedObject = null;
    dragOrigin = null;
    svg.removeChild(delNode);
}

//mouse position
function mousePos(event) {
	var svgPoint = svg.createSVGPoint();

    svgPoint.x = event.clientX;
    svgPoint.y = event.clientY;

    svgPoint = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
    
    return svgPoint;
}

//set transform translate for element group
function setGroupTranslate(group, x, y){
	for (var g= 0; g < group.length; ++g){
		var transf = getTranslPos(group[g]);
		transf.tr.setTranslate(x, y);
	}
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

//return rounded difference between initial and current position 
function getRoundDiffPos(p2, p1){
	return roundPos(p2 - p1);
}

//round position to two decimals	
function roundPos(pos){
	return Math.round(pos * 100) / 100;
}


