using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading;

internal static class LanzadorTutorEdo
{
    private static int Main()
    {
        string carpeta = Path.GetDirectoryName(Process.GetCurrentProcess().MainModule.FileName);
        string python = Path.Combine(carpeta, "python", "python.exe");
        string app = Path.Combine(carpeta, "app.py");
        if (!File.Exists(python) || !File.Exists(app))
        {
            return Error("Faltan archivos del paquete. Mantén TutorEDO.exe dentro de la carpeta completa Tutor_EDO_Portable.");
        }

        int puerto = BuscarPuerto();
        if (puerto == 0)
        {
            return Error("No encontré un puerto local disponible entre 8501 y 8599.");
        }

        Process proceso;
        try
        {
            var inicio = new ProcessStartInfo
            {
                FileName = python,
                Arguments = "-m streamlit run \"" + app + "\" --server.headless true --server.address 127.0.0.1 --server.port " + puerto,
                WorkingDirectory = carpeta,
                UseShellExecute = false
            };
            inicio.EnvironmentVariables["PYTHONUTF8"] = "1";
            inicio.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            proceso = Process.Start(inicio);
        }
        catch (Exception ex)
        {
            return Error("No se pudo iniciar Tutor EDO: " + ex.Message);
        }

        string url = "http://127.0.0.1:" + puerto;
        Console.WriteLine("Iniciando Tutor EDO. Espera mientras carga; Ctrl+C lo detiene.");
        if (!EsperarServidor(proceso, url))
        {
            if (!proceso.HasExited)
            {
                proceso.Kill();
                proceso.WaitForExit();
            }
            return Error("La aplicación no respondió al iniciar. Revisa los mensajes anteriores.");
        }

        Console.WriteLine("Tutor EDO está listo: " + url);
        try
        {
            Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
        }
        catch (Exception ex)
        {
            Console.WriteLine("No se abrió el navegador automáticamente: " + ex.Message);
            Console.WriteLine("Abre esta dirección manualmente: " + url);
        }

        proceso.WaitForExit();
        return proceso.ExitCode;
    }

    private static int BuscarPuerto()
    {
        for (int puerto = 8501; puerto <= 8599; puerto++)
        {
            try
            {
                var escucha = new TcpListener(IPAddress.Loopback, puerto);
                escucha.Start();
                escucha.Stop();
                return puerto;
            }
            catch (SocketException)
            {
            }
        }
        return 0;
    }

    private static bool EsperarServidor(Process proceso, string url)
    {
        for (int intento = 0; intento < 120; intento++)
        {
            if (proceso.HasExited)
            {
                return false;
            }

            try
            {
                var solicitud = (HttpWebRequest)WebRequest.Create(url + "/_stcore/health");
                solicitud.Timeout = 500;
                solicitud.GetResponse().Close();
                return true;
            }
            catch (WebException)
            {
                Thread.Sleep(500);
            }
        }
        return false;
    }

    private static int Error(string mensaje)
    {
        Console.Error.WriteLine(mensaje);
        Console.WriteLine("Presiona una tecla para cerrar.");
        Console.ReadKey();
        return 1;
    }
}
