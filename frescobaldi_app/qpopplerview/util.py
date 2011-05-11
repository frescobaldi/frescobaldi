
from PyQt4.QtCore import QFile, QIODevice
from PyQt4.QtGui import QPrinter

def psfile(doc, printer, output, pageList=None, margins=(0, 0, 0, 0)):
    """Writes a PostScript rendering of a Poppler::Document to the output.
    
    doc: a Poppler::Document instance
    printer: a QPrinter instance from which the papersize is read
    output: a filename or opened QIODevice (will not be closed)
    pageList: a list of page numbers. By default the pagerange is read
        from the QPrinter instance. Page numbers start with 1.
    margins: a sequence of four values describing the margins (left, top, right,
        bottom), all defaulting to 0.
    
    Returns True on success, False on error.
    
    """
    ps = doc.psConverter()
    
    if pageList is None:
        if (printer.printRange() == QPrinter.AllPages
            or (printer.fromPage() == 0 and printer.toPage() == 0)):
            pageList = list(range(1, doc.numPages() + 1))
        else:
            pageList = list(range(printer.fromPage(), printer.toPage() + 1))
    else:
        for num in pageList:
            if num < 1:
                raise ValueError, "page numbers must be 1 or higher"
    
    ps.setPageList(pageList)
        
    if isinstance(output, QIODevice):
        ps.setOutputDevice(output)
    else:
        ps.setOutputFileName(output)
    
    paperSize = printer.paperSize(QPrinter.Point)
    ps.setPaperHeight(paperSize.height())
    ps.setPaperWidth(paperSize.width())
    
    left, top, right, bottom = margins
    ps.setLeftMargin(left)
    ps.setTopMargin(top)
    ps.setRightMargin(right)
    ps.setBottomMargin(bottom)
    return ps.convert()


