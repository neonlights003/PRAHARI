PDF = prahari_technical_report.pdf
TEX = prahari_technical_report.tex

all: $(PDF)

$(PDF): $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)
	pdflatex -interaction=nonstopmode $(TEX)

clean:
	rm -f *.aux *.log *.toc *.out *.lof *.lot *.lol
