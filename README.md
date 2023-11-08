# CHALLENGE_FINGERPRINT
<p>El challenge consiste en crear un sistema de autenticación que utilice la información capturada por el sensor de huellas dactilares para verificar la identidad de un usuario. Para lograrlo, se empleará la "winbio.dll" para interactuar con el hardware del lector de huellas. Esto incluirá la captura de la huella dactilar y la gestión de los datos biométricos.</p>
<p>este challenge tiene dos modos de funcionamiento: modo parental y modo empresarial </p>
<h2>modo parental</h2>
<p>devuelve 0 si no esta registrada la huella dactilar y un 1 si esta registrada</p>
<h2>modo emresarial</h2>
<p>devuelve un numero random del 2 al 100 si no esta registrada la huella dactilar y un 1 si esta registrada</p>

ejemplo de configuracion
```json
{
	"FileName": "challenge_loader_python.dll",
	"Description": "challenge_fingerprint",
	"Props": {
		"module_python": "challenge_fingerprint",
		"validity_time": 3600,
		"refresh_time": 3000,
                             "metodo":"empresarial",

		"url":"C:\\Users\\gomezbot\\source\\repos\\DLL_VALIDATOR-NOKIA\\x64\\Release\\"
	},
	"Requirements": "none"
}

```
