Proceso OrdenacionPorSeleccion
    Definir lista Como Entero
    Escribir "Ingrese el tamaño del arreglo:"
    Leer n
    Dimension lista[n]
    
    Para i = 1 Hasta n Hacer
        Escribir "Ingrese el elemento ", i, ":"
        Leer lista[i]
    Fin Para
    
    Para i = 1 Hasta n-1 Hacer
        minimo = i
        Para j = i+1 Hasta n Hacer
            Si lista[j] < lista[minimo] Entonces
                minimo = j
            Fin Si
        Fin Para
        // Intercambiar elementos
        temp = lista[i]
        lista[i] = lista[minimo]
        lista[minimo] = temp
    Fin Para
    
    Escribir "Lista ordenada:"
    Para i = 1 Hasta n Hacer
        Escribir lista[i]
    Fin Para
Fin Proceso
