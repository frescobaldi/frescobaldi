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
var clone, delNode;
var doClick = true;

///////////////////////////////////////////////
// Helper functions
///////////////////////////////////////////////

//mouse position
function mousePos(event) {
    this.__doc__ = 
    "Retrieves the mouse position of an event" +
    "and translates it to useful coordinates";
    
    var svgPoint = svg.createSVGPoint();
    svgPoint.x = event.clientX;
    svgPoint.y = event.clientY;
    svgPoint = svgPoint.matrixTransform(svg.getScreenCTM().inverse());
    return svgPoint;
}

function getTranslPos(elem) {
    this.__doc__ =
    "Return the coordinates and the transform object" +
    "from a given SVG element if it has the right type.";
    
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

function round(digits, number) {
    this.__doc__ =
    "set the precision of the given float" +
    "to a given number of digits.";
    
    var factor = Math.pow(10, digits)
    return Math.round(number * factor) / factor
}

//set transform translate for element group
function setGroupTranslate(group, x, y) {
    this.__doc__ =
    "Translate a group of SVG items to a new position." +
    "The items of the group are translated relatively" +
    "to the position of the group.";
    
    var groupOrigin = getTranslPos(group[0]);
    for (var g = 0; g < group.length; ++g) {
        var subItem = getTranslPos(group[g]);
        
        var xOff = subItem.x - groupOrigin.x;
        var yOff = subItem.y - groupOrigin.y;
        
        subItem.tr.setTranslate(x + xOff, y + yOff);
    }
}

function enableMouseEvents(elem) {
    this.__doc__ =
    "Enable the event handlers for a given SVG element." +
    "This is sometimes necessary as a cleanup after operations.";
    
    elem.onmousedown = MouseDown;
    elem.onmousemove = MouseMove;
    elem.onmouseup = MouseUp;
}

// Is the name of this function appropriate?
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
    this.__doc__ =
    "Event handler for errors of the SVG window." +
    "For now simply write to the console."
    
    pyLinks.pyLog(e.message);
}

///////////////////////////////////////////////
// Worker functions
///////////////////////////////////////////////

function collectElements(){
    this.__doc__ =
    "Iterates over draggable elements and prepares them for editing." +
    "All elements having a 'transform' attribute are enabled for dragging." +
    "Groups of elements (such as e.g. results from a \tempo command" +
    "are collected into groups so they can be dragged together.";
    
    var t;
    for (t = 0; t < draggable.length; ++t) {
    
        // process elements that have a link themselves
        if (draggable[t].hasAttribute("transform")) {
            enableTranslPositioning(draggable[t])
        }
    
        var node = draggable[t].firstChild;
        var children = new Array();
    
        // determine nodes with groups of children
        while (node) {
            if (node.nodeType == 1 && node.hasAttribute("transform")) {    
                children.push(node);
                enableTranslPositioning(node)
            }
            node = node.nextSibling;
        }
        // and group elements as a property of the parent element
        if (children.length > 1) {
            draggable[t].group = children;
        }
    }
}

///////////////////////////////////////////////
// Classes
///////////////////////////////////////////////

// It's not clear whether we should keep that class at all.
// The current implementation relies very much on the pure member variables,
// but maybe it will become useful in a later stage.
function Point(x, y) {
    this.x = x;
    this.y = y;
    this.precision = 2;

    this.translate = function (otherPoint) {
        return new Point(this.x + otherPoint.x, this.y + otherPoint.y);
    };

    this.distanceTo = function (otherPoint) {
        distX = round(this.precision, otherPoint.x - this.x);
        distY = round(this.precision, otherPoint.y - this.y);
        return new Point(distX, distY);
    };

    // Debugging function for easy display of coordinates
    this.toString = function () {
        return "X: " + this.x + " | Y: " + this.y;
    };
}

// Class representing a draggable (text?) element
function DraggableObject(elem, e) {
    
    this.__doc__ =
    "A draggable SVG object." +
    "The class stores the necessary positioning values " +
    "and is able to calculate the remaining values. " +
    "Instantiate it by passing the SVG elements 'elem' " +
    "and the mouse event 'e'. " +
    "For recalculating values call 'updatePositions()' " +
    "with a mouse event. " +
    "Properties return Point() instances but the X and Y " +
    "coordinates can be accessed directly too. " +
    "A JSON representation is implemented as a draft.";
    
    this.target = e.target;
    
    this.textedit = elem.parentNode.getAttribute('xlink:href');

    // Reference points for dragging operation
    var mp = mousePos(e);
    this.startDragX = mp.x;
    this.startDragY = mp.y;
    this.currDragX = this.currDragY = 0;

    // original (LilyPond's) position of the object
    //TODO: Currently this gives wrong results when there already is an 
    // extra-offset override in the LilyPond source
    this.initX = parseFloat(elem.getAttribute("init-x"));
    this.initY = parseFloat(elem.getAttribute("init-y"));

    // current position at the start of a (new) drag
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
    
    this.currDrag = function () {
        // current dragging offset, 
        // calculated from initial and current mouse position.

        return new Point(this.currDragX, this.currDragY);
    };

    this.currOffset = function () {
        // current offset,
        // = current relative to initial position
        
        return new Point(this.currOffX, this.currOffY);
    };

    this.currPos = function () {
        // current object position,
        // calculated from starting position and current drag offset
        
        return new Point(this.currX, this.currY);
    };

    this.initPos = function () {
        // initial position of the element
        // the one compiled by LilyPond

        return new Point(initX, initY);
    };
    
    this.JSONified = function() {
        // return a JSON string representing relevant information on the object
        
        return JSON.stringify(this,
            ["textedit",
             "initX",
             "initY",
             "startX",
             "startY",
             "currX",
             "currY"]);
    };
    
    this.modified = function() {
        // determine if an object is changed compared to the initial position.
        return (round(2, this.currX) != round(2, this.initX)) || (round(2, this.currY) != round(2, this.initY))
    };

    this.startPos = function() {
        // position at the start of the dragging operation
        return new Point(this.startX, this.startY);
    };
    
    this.translate = function() {
        if (this.group) {
            var i;
            for (i = 0; i < this.group.length; ++i) {
                var subItem = getTranslPos(group[i]);
                subItem.tr.setTranslate(this.currX, this.currY);
            }
        } else { 
            this.transform.setTranslate(this.currX, this.currY);
        }
    };

    this.updatePositions = function (e) {
        // recalculate the position variables upon modified mouse position.
        var mp = mousePos(e);
        this.currDragX = mp.x - this.startDragX;
        this.currDragY = mp.y - this.startDragY;
        this.currX = this.startX + this.currDragX;
        this.currY = this.startY + this.currDragY;
        this.currOffX = this.startOffX + this.currDragX;
        this.currOffY = this.startOffY - this.currDragY;
        
        this.translate();
        
    };
}

///////////////////////////////////////////////
// Event handlers
///////////////////////////////////////////////

function MouseDown(e) {
    this.__doc__ =
    "Creates an object representing the dragged SVG object " +
    "and triggers a number of signals. " +
    "Makes a clone of the SVG object and copies it " +
    "to the end of the tree so it will always be on top.";
    
    e.stopPropagation();

    draggedObject = new DraggableObject(this, e);
    
    // TODO: Determine if "this" is part of a group (no idea how to access that)
    // if yes: add the group to draggedObject as a property.

    // send signals
    pyLinks.dragElement(draggedObject.textedit)
    pyLinks.startDragging(draggedObject.currOffX, draggedObject.currOffY);
    pyLinks.draggedObject(draggedObject.JSONified());

    // create a clone of the dragged SVG object so the 
    // dragged object will always be over other elements.
    clone = this.cloneNode(true);
    this.parent = this.parentNode;
    this.parentNode.replaceChild(clone, this);
    svg.appendChild(this);

    //store a reference for deletion
    delNode = this;

    //make the clone transparent
    //This could later be made a preference.
    clone.setAttribute("opacity", "0.3");
}

function MouseMove(e) {
    this.__doc__ =
    "Only respond to events from a dragged element. " +
    "Update the properties of the object by passing the mouse event " +
    "and move the object (or its group) to the appropriate new position.";
    
    e.stopPropagation();

    if (draggedObject && e.target == draggedObject.target) {
        draggedObject.updatePositions(e);

        // TODO: Completely remove this and let updatePositions do all the work!s
        var currPos = draggedObject.currPos();
        if (this.parent && this.parent.group) {
            setGroupTranslate(this.parent.group, currPos.x, currPos.y);
//        } else {
//            draggedObject.transform.setTranslate(currPos.x, currPos.y);
        }

        pyLinks.dragging(draggedObject.currOffX, draggedObject.currOffY);
        
        //disable click
        doClick = false;
    }
}

function MouseUp(e) {
    this.__doc__ =
    "Replace the cloned object with the original and " +
    "determine if the object has been modified and color it.";    

    e.stopPropagation();
    if (draggedObject && e.target == draggedObject.target) {

        var clonePos = getTranslPos(clone);
        cloneTransform = clonePos.tr;
        cloneTransform.setTranslate(draggedObject.currX, draggedObject.currY);

        clone.removeAttribute("opacity");
        
        // I think this should be moved to a function
        // because there will be more cases to cover.
        if (draggedObject.modified()) {
            if (clone.getAttribute("fill") != "orange") {
                clone.setAttribute("fill", "orange");
            }
        } else {
            if (clone.getAttribute("fill") == "orange") {
                clone.removeAttribute("fill");
            }
        }

        enableMouseEvents(clone);
        
        //if no drag is performed treat the event as a click
        if(doClick){
            pyLinks.click(draggedObject.textedit);
        }else{
            pyLinks.dragged(draggedObject.currOffX, draggedObject.currOffY);
            doClick = true; //unset drag
        }

        // clean up
        draggedObject = null;
        svg.removeChild(delNode);
    }
}

////////////////////////////////////////////
// Actual execution block
////////////////////////////////////////////

collectElements();
