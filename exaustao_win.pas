// ============================================================
//  INDICADOR DE EXAUSTÃO - MINI ÍNDICE (WIN)
//  Autor  : Mesa Proprietária
//  Versão : 1.0
//
//  Conceito:
//    Identifica zonas de compra e venda fortes combinando
//    Bandas de ATR (distância estatística da EMA) com o IFR.
//    Quando o preço atinge a banda E o IFR confirma, há alta
//    probabilidade de exaustão e reversão.
//
//  Zonas:
//    Zona 1 (amarelo) - Alerta        : 1.5x ATR da EMA
//    Zona 2 (laranja) - Forte         : 2.5x ATR da EMA
//    Zona 3 (vermelho/verde) - Extremo: 3.5x ATR da EMA
//
//  Coloração de barra:
//    Laranja  = Exaustão de venda (zona forte + IFR > 70)
//    Roxo     = Exaustão extrema de venda (zona extrema)
//    Ciano    = Exaustão de compra (zona forte + IFR < 30)
//    Azul     = Exaustão extrema de compra (zona extrema)
// ============================================================

input
  PeriodoEMA   (21);    // Período da média central
  PeriodoATR   (14);    // Período do ATR
  PeriodoIFR   (9);     // Período do IFR (RSI rápido para day trade)
  Mult1        (1.5);   // Multiplicador zona de alerta
  Mult2        (2.5);   // Multiplicador zona forte
  Mult3        (3.5);   // Multiplicador zona extrema
  NivelIFRAlto (70);    // IFR sobrecomprado
  NivelIFRBaixo(30);    // IFR sobrevendido

var
  EMA1        : Float;
  ATR1        : Float;
  IFR1        : Float;
  // Bandas superiores (zonas de venda)
  BandaSup1   : Float;
  BandaSup2   : Float;
  BandaSup3   : Float;
  // Bandas inferiores (zonas de compra)
  BandaInf1   : Float;
  BandaInf2   : Float;
  BandaInf3   : Float;
  // Flags de exaustão
  ExaustaoVenda   : Boolean;
  ExaustaoCompra  : Boolean;
  ExaustaoVendaEx : Boolean;
  ExaustaoCompraEx: Boolean;

begin
  // --- Cálculos principais ---
  EMA1 := MediaExp(Close, PeriodoEMA);
  ATR1 := MedAmplitude(PeriodoATR);
  IFR1 := IFR(Close, PeriodoIFR);

  // --- Bandas superiores (pressão vendedora) ---
  BandaSup1 := EMA1 + (ATR1 * Mult1);
  BandaSup2 := EMA1 + (ATR1 * Mult2);
  BandaSup3 := EMA1 + (ATR1 * Mult3);

  // --- Bandas inferiores (pressão compradora) ---
  BandaInf1 := EMA1 - (ATR1 * Mult1);
  BandaInf2 := EMA1 - (ATR1 * Mult2);
  BandaInf3 := EMA1 - (ATR1 * Mult3);

  // --- Detecção de exaustão ---
  // Exaustão de venda: preço na zona forte E IFR sobrecomprado
  ExaustaoVenda    := (Close >= BandaSup2) and (IFR1 >= NivelIFRAlto);
  // Exaustão extrema: preço além da zona extrema
  ExaustaoVendaEx  := (Close >= BandaSup3);

  // Exaustão de compra: preço na zona forte E IFR sobrevendido
  ExaustaoCompra   := (Close <= BandaInf2) and (IFR1 <= NivelIFRBaixo);
  // Exaustão extrema: preço além da zona extrema
  ExaustaoCompraEx := (Close <= BandaInf3);

  // --- Plotagem das linhas ---
  // EMA central (branca)
  SetPlotColor(1, clWhite);
  SetPlotWidth(1, 2);
  SetPlotStyle(1, psDot);
  Plot(EMA1);

  // Zona de alerta superior (amarelo fraco)
  SetPlotColor(2, RGB(180, 140, 0));
  SetPlotWidth(2, 1);
  Plot2(BandaSup1);

  // Zona forte superior (laranja)
  SetPlotColor(3, clOrange);
  SetPlotWidth(3, 2);
  Plot3(BandaSup2);

  // Zona extrema superior (vermelho)
  SetPlotColor(4, clRed);
  SetPlotWidth(4, 2);
  Plot4(BandaSup3);

  // Zona de alerta inferior (amarelo fraco)
  SetPlotColor(5, RGB(180, 140, 0));
  SetPlotWidth(5, 1);
  Plot5(BandaInf1);

  // Zona forte inferior (ciano)
  SetPlotColor(6, clAqua);
  SetPlotWidth(6, 2);
  Plot6(BandaInf2);

  // Zona extrema inferior (verde)
  SetPlotColor(7, clLime);
  SetPlotWidth(7, 2);
  Plot7(BandaInf3);

  // --- Coloração das barras (sinal visual de exaustão) ---
  if ExaustaoVendaEx then
    PaintBar(clFuchsia)           // Roxo = exaustão extrema de venda
  else if ExaustaoVenda then
    PaintBar(clOrange)            // Laranja = exaustão de venda forte
  else if ExaustaoCompraEx then
    PaintBar(clBlue)              // Azul = exaustão extrema de compra
  else if ExaustaoCompra then
    PaintBar(clAqua);             // Ciano = exaustão de compra forte

end;
