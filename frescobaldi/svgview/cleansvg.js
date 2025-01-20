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
//To be able to save the SVG edits without traces of the editing process
//use this script

window.addEventListener('error', error, false);

//write error message
function error(e) {
    pyLinks.pyLog(e.message);
}

var svgarr = document.getElementsByTagName("svg");
var svg = svgarr[0];
cleanTree(svg);

//clean node and all siblings and childs 
function cleanTree(node){
	
	//pass on recursively		
	if(node.hasChildNodes()){
		cleanTree(node.firstChild);
	}
	
	sibl = node.nextSibling;
	if(sibl){
		cleanTree(sibl);
	}
	
    //do the actual cleaning
	doClean(node);
}

function doClean(node){
	
	if(node.nodeType == 1 && node.hasAttribute("init-x")){
		node.removeAttribute("init-x");
		node.removeAttribute("init-y");
	}

	if(node.nodeType == 1 && node.getAttribute("fill") == "orange"){
		node.setAttribute("fill", "currentColor");
	}
}

