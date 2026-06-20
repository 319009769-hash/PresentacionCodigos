' Este codigo ha sido generado por el modulo psexport 20180802-w32 de PSeInt.
' Es posible que el codigo generado no sea completamente correcto. Si encuentra
' errores por favor reportelos en el foro (http://pseint.sourceforge.net).

Module ORDENACIONPORSELECCION

	Sub Main()
		Dim i As Integer
		Dim j As Integer
		Dim minimo As Integer
		Dim n As Integer
		Dim temp As String
		Console.WriteLine("Ingrese el tamaño de la lista:")
		n = Integer.Parse(Console.ReadLine())
		Dim lista(n) As Integer
		For i=1 To n
			Console.WriteLine("Ingrese el elemento ",i,":")
			lista(i) = Integer.Parse(Console.ReadLine())
		Next i
		For i=1 To n-1
			minimo = i
			For j=i+1 To n
				If lista(j)<lista(minimo) Then
					minimo = j
				End If
			Next j
			' Intercambiar elementos
			temp = lista(i)
			lista(i) = lista(minimo)
			lista(minimo) = temp
		Next i
		Console.WriteLine("Lista ordenada:")
		For i=1 To n
			Console.WriteLine(lista(i))
		Next i
	End Sub

End Module
