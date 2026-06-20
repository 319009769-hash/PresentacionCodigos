/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Main.java to edit this template
 */
package arrunidemensional;

import java.util.Scanner;

/**
 *
 * @author Gonzalez Gonzalez Luis Armando   11/09/2024
 */
public class ArrUnidemensional {

    /**
     * @param args the command line arguments
     */

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        //Mi teclado no tiene la letra enie :(
        System.out.print("Ingresa el tamanio del arreglo papi: ");
        //int por ser numeros enteros
        int n = scanner.nextInt();

        // Crea el arreglo
        int[] arreglo = new int[n];

        // Llenar el arreglo con nurmes ingresados por el usuario
        //for(int i palabra.tointArray(n)????)
        for (int i = 1; i < n; i++) {
            System.out.print("Ingresa el numero para el num del arregro " + i + ": ");
            arreglo[i] = scanner.nextInt();
        }

        // Este muestra el contenido del arreglo
        System.out.println("El arreglo ingresado es: ");
        for (int i = 1; i < n; i++) {
            System.out.print(arreglo[i] + " ");
            //La verdad no supe como se implementa el: Objet o = new Object[n] -o- Object [] o = new Object
        }
    }
}

