Algoritmo InsertionSort
	temp = 0
	n = 150
	dimension ListNum[n]
	
	para c<-1 hasta n hacer
		ListNum[c] <-aleatorio(10,50)
		imprimir sin saltar ListNum[c] " "
	FinPara
	
	para c<-2 hasta n Hacer
		temp<-ListNum[c]
		ci<-c-1
		mientras ci>0 y ListNum[ci]>temp
			ci<-ci-1
		FinMientras
		ListNum[ci+1]<-temp
	FinPara
	
	Imprimir " "
	Imprimir " "
	
	para c<-1 hasta n hacer
		imprimir sin saltar ListNum[c] " "
	FinPara
FinAlgoritmo
