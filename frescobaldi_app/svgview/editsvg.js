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

/*********************************************
*
* File structure:
* - global variables
* - (helper) functions (sorted alphabetically)
* - (worker) function(s)
* - (helper) class(es)
* - Event handlers
* - Actual execution block
*/

var svgarr = document.getElementsByTagName("svg");
var svg = svgarr[0];
var maxX = svg.offsetWidth - 1;
var maxY = svg.offsetHeight - 1;
var draggable = document.getElementsByTagName('a');
var draggedObject = null;

var draggedObject = null;
var clone, delNode;

///////////////////////////////////////////////
// Helper function
///////////////////////////////////////////////

//mouse position
function mousePos(event) {
    var svgPoint = svg.createSVGPoint();

    svgPoint.x = event.clientX;
    svgPoint.y = event.clientY;

    svgPoint = svgPoint.matrixTransform(svg.getScreenCTM().inverse());

    return svgPoint;
}

//return rounded difference between initial and current position 
function getRoundDiffPos(p2, p1) {
    return roundPos(p2 - p1);
}

//get markup translate coordinates
function getTranslPos(elem) {
    var tr = elem.transform.baseVal.getItem(0);
    if (tr.type == SVGTransform.SVG_TRANSFORM_TRANSLATE) {
        return {
            x: tr.matrix.e,
            y: tr.matrix.f,
            tr: tr
        }
    }
}

//I'm putting this back in at least for now
//generic onmouseup
//needed when dragging doesn't keep mouse over object
onmouseup = function (e) {
    MouseUp(e);
};

//round position to two decimals	
function roundPos(pos) {
    return Math.round(pos * 100) / 100;
}

function round(digits, number) {
    var factor = Math.pow(10, digits)
    return Math.round(number * factor) / factor
}

//set transform translate for element group
function setGroupTranslate(group, x, y) {
    for (var g = 0; g < group.length; ++g) {
        var transf = getTranslPos(group[g]);
        transf.tr.setTranslate(x, y);
    }
}

function enableMouseEvents(elem) {
    elem.onmousedown = MouseDown;
    elem.onmousemove = MouseMove;
    elem.onmouseup = MouseUp;
}

function enableTranslPositioning(node) {
    enableMouseEvents(node);

    //check first if init attribute is already set
    if(!node.hasAttribute("init-x")){
        var p = getTranslPos(node);
        node.setAttribute("init-x", p.x);
        node.setAttribute("init-y", p.y);
    }
}

//write error message
function error(e) {
    pyLinks.pyLog(e.message);
}


/////////////////////////////////////////////
//listen for drag events on all text elements
//and save their initial position
function collectElements(){
    var t;
    for (t = 0; t < draggable.length; ++t) {
    
        //transform attribute can be in link element itself
        if (draggable[t].hasAttribute("transform")) {
            enableTranslPositioning(draggable[t])
        }
    
        var node = draggable[t].firstChild;
    
        var childs = new Array();
    
        //loop through the children of every draggable node
        while (node) {
            // so far only enable dragging of 
            // nodes with the transform attribute
            if (node.nodeType == 1 && node.hasAttribute("transform")) {
    
                childs.push(node);
    
                enableTranslPositioning(node)
    
            }
            node = node.nextSibling;
        }
        //group elements together if the belong to the same link tag
        if (childs.length > 1) {
            draggable[t].group = childs;
        }
    }
}


// It's not clear whether we should keep that class at all.
// The current implementation relies very much on the pure member variables.
function Point(x, y) {
    this.x = x;
    this.y = y;

    this.translate = function (otherPoint) {
        return new Point(this.x + otherPoint.x, this.y + otherPoint.y);
    };

    this.distanceTo = function (otherPoint) {
        distX = getRoundDiffPos(otherPoint.x, this.x);
        distY = getRoundDiffPos(otherPoint.y, this.y);
        return new Point(distX, distY);
    };

    // Debugging function for easy display of coordinates
    this.toString = function () {
        return "X: " + this.x + " | Y: " + this.y;
    };
}

// Class representing a draggable (text?) element
function DraggableObject(elem, e) {
    // elem is the clicked item itself,
    // e the mouse event

    // I'm not really sure about what this "target" actually *is*.
    this.target = e.target;
    
    // store the textedit url attached to the element
    this.url = elem.parentNode.getAttribute('xlink:href');

    // Reference points for dragging operation
    var mp = mousePos(e);
    this.startDragX = mp.x;
    this.startDragY = mp.y;
    this.currDragX = this.currDragY = 0;

    // load original (LilyPond's) position of the object
    //TODO: Currently this seems to get wrong results with items that have been
    //moved in a previous session. 
    // initPos seems to return the same as startPos in any case (which shouldn't be the case)
    this.initX = parseFloat(elem.getAttribute("init-x"));
    this.initY = parseFloat(elem.getAttribute("init-y"));

    // determine the current position at the start of a (new) drag
    this.transform = elem.transform.baseVal.getItem(0);
    if (this.transform.type == SVGTransform.SVG_TRANSFORM_TRANSLATE) {
        this.startX = this.transform.matrix.e;
        this.startY = this.transform.matrix.f;
        this.currX = this.startX;
        this.currY = this.startY;
        this.startOffX = this.startX - this.initX;
        this.currOffX = this.startOffX;
        this.startOffY = this.initY - this.startY;
        this.currOffY = this.startOffY;
    }

    // Properties, implemented as privileged methods    
    // current dragging offset, 
    //calculated from initial and current mouse position.
    this.currDrag = function () {
        return new Point(this.currDragX, this.currDragY);
    };

    this.currOffset = function () {
        return new Point(this.currOffX, this.currOffY);
    };

    // current object position,
    // calculated from starting position and current drag offset
    this.currPos = function () {
        return new Point(this.currX, this.currY);
    };

    // initial (i.e. LilyPond-compiled) position of the element
    this.initPos = function () {
        return new Point(initX, initY);
    };
    
    // return a JSON string representing relevant information on the object
    this.JSONified = function() {
        return JSON.stringify(this,
            ["url",
             "initX",
             "initY",
             "startX",
             "startY",
             "currX",
             "currY"]);
    };
    
    // determine if an object is changed compared to the initial position.
    this.modified = function() {
        return (roundPos(this.currX) != roundPos(this.initX)) || (roundPos(this.currY) != roundPos(this.initY))
    };

    this.startPos = function () {
        return new Point(this.startX, this.startY);
    };

    // recalculate the position variables upon modified mouse position.
    this.updatePositions = function (e) {
        var mp = mousePos(e);
        this.currDragX = mp.x - this.startDragX;
        this.currDragY = mp.y - this.startDragY;
        this.currX = this.startX + this.currDragX;
        this.currY = this.startY + this.currDragY;
        this.currOffX = this.startOffX + this.currDragX;
        this.currOffY = this.startOffY - this.currDragY;
    };
}

function MouseDown(e) {
    e.stopPropagation();

    // create an object representing the dragged item
    draggedObject = new DraggableObject(this, e);

    //catch type of element by sending link
    pyLinks.dragElement(draggedObject.url)

    // announce original position (may already have an offset)
    pyLinks.startDragging(draggedObject.currOffX, draggedObject.currOffY);
    
    // send the SVG information of the dragged object to Python
    pyLinks.draggedObject(draggedObject.JSONified());

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
    //This could later be made a preference.
    clone.setAttribute("opacity", "0.3");
}

function MouseMove(e) {
    e.stopPropagation();
    // ignore events from other objects than the dragged one
    // This doesn't work reliably yet. When an object is dragged
    // _under_ another one the event is only triggered for the wrong one.
    if (draggedObject && e.target == draggedObject.target) {

        draggedObject.updatePositions(e);

        // move the object to the new position
        var currPos = draggedObject.currPos();
        if (this.parent && this.parent.group) {
            // move whole group together
            // to-do: calculate position for each element in the group
            pyLinks.pyLog(draggedObject.transform.toString());
            setGroupTranslate(this.parent.group, currPos.x, currPos.y);
        } else {
            draggedObject.transform.setTranslate(currPos.x, currPos.y);
        }

        // announce the new position
        pyLinks.dragging(draggedObject.currOffX, draggedObject.currOffY);
    }
}

function MouseUp(e) {

    e.stopPropagation();
    if (draggedObject && e.target == draggedObject.target) {

        //set the new position for the clone
        var clonePos = getTranslPos(clone);
        cloneTransform = clonePos.tr;
        cloneTransform.setTranslate(draggedObject.currX, draggedObject.currY);

        //remove transparency
        clone.removeAttribute("opacity");

        //change color when object is modified
        //reset color when object is moved to initial position.
        if (draggedObject.modified()) {
            if (clone.getAttribute("fill") != "orange") {
                clone.setAttribute("fill", "orange");
            }
        } else {
            if (clone.getAttribute("fill") == "orange") {
                clone.removeAttribute("fill");
            }
        }

        //enable further editing
        enableMouseEvents(clone);

        pyLinks.dragged(draggedObject.currOffX, draggedObject.currOffY);

        // clean up
        draggedObject = null;
        svg.removeChild(delNode);
    }
}

////////////////////////////////////////////
// Actual execution block
////////////////////////////////////////////

collectElements();
