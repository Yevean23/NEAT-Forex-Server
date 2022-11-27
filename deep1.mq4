//+------------------------------------------------------------------+
//|                                                        deep1.mq4 |
//|                                                              yev |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "yev"
#property link      ""
#property version   "1.00"
#property strict
int ticket = 0;
int time = 1;
datetime LastAction = Time[0];
//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//---
   restart();
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//---
   
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
//--
   
   if(LastAction != Time[0]){
   //if(MathMod(time,4.0)==0){ 
   
   double last_candle = 100000*(Open[1] - Close[1]);
   double last_volume = Volume[1];
   double slope = 100000*(Close[0] - Close[11]);
   double unrealized_gains;
   
   if(ticket){
      OrderSelect(ticket, SELECT_BY_TICKET, MODE_TRADES);
      unrealized_gains = OrderProfit();
   }else{
      unrealized_gains = 0.0;
   }


   string cookie=NULL,headers;
   char post[],result[];
   string str = "balance="+DoubleToStr(AccountBalance())+"&last_candle="+DoubleToStr(last_candle)+"&last_volume="+DoubleToStr(last_volume)+"&slope="+DoubleToStr(slope)+"&Ask="+DoubleToStr(Ask)+"&Bid="+DoubleToStr(Bid);
   int res;
   int timeout=5000; //--- Timeout below 1000 (1 sec.) is not enough for slow Internet connection
   ResetLastError();
   string url = "http://127.0.0.1/users" + "?" + str;
   //Print(url);
   res=WebRequest("GET",url,cookie,NULL,5000,post,0,result,headers);
   
   int tit = ArraySize(result)-1;
   string html = "";
   for(int xx=0;xx<=tit;xx++){
      html+= CharToStr(result[xx]);
   }
   
   //Print(html);
   
   string to_split=html;   // A string to split into substrings
   StringReplace(to_split,"[","");
   StringReplace(to_split,"]","");
   StringReplace(to_split,"\"","");
   StringReplace(to_split," ","");
   string sep=",";                // A separator as a character
   ushort u_sep;                  // The code of the separator character
   string resultu[];               // An array to get strings

   
   
   //Print(to_split);
   //--- Get the separator code
   u_sep=StringGetCharacter(sep,0);
   //--- Split the string to substrings
   int k=StringSplit(to_split,u_sep,resultu);
   //--- Now output all obtained strings
   //Print("k : " + k);
   int resl[];
   ArrayResize(resl,k);
   if(k>1){
      for(int i=0;i<k;i++){
         //Print(resultu[i]);
         string sep2=":";                // A separator as a character
         ushort u_sep2;                  // The code of the separator character
         string parse[];
         //--- Get the separator code
         u_sep2=StringGetCharacter(sep2,0);
         //--- Split the string to substrings
         int k2=StringSplit(resultu[i],u_sep2,parse);
         //--- Now output all obtained strings
         if(k2>1){
            int magicnum = StringToInteger( parse[0]);
            int decision = StringToInteger( parse[1]);
            //Print(magicnum + " : " + decision);
            
            if(decision == 1 && !check_order_by_magic_number(magicnum)){
               OrderSend(Symbol(),OP_BUY,1,Ask,0,0,0,"NEAT",magicnum,0,clrGreen);
            }
            else if(decision == 2 && !check_order_by_magic_number(magicnum)){
               OrderSend(Symbol(),OP_SELL,1,Bid,0,0,0,"NEAT",magicnum,0,clrGreen);
            }
            
            if(check_order_by_magic_number(magicnum)){
               ticket = get_order_by_magic_number(magicnum);
               if(decision == -1){
                  if( OrderType() == OP_BUY ){
                     OrderClose(ticket,1,Bid,0,Red);
                  } else {
                     OrderClose(ticket,1,Ask,0,Red);
                  }
                  
               }
            }
         }        

      }
   }
   
   
   
   
   }
   if(( (AccountEquity() / AccountBalance()) >= 1.03 )|| ( (AccountEquity() / AccountBalance()) <= 0.77 )){
      restart();
   }
   LastAction = Time[0];
   time+=1;
  }
//+------------------------------------------------------------------+

bool check_order_by_magic_number(int mg){
   for(int x = 0; x < OrdersTotal(); x++){
      OrderSelect(x,SELECT_BY_POS,MODE_TRADES);
      if(OrderMagicNumber() == mg){
         return true;
      }
   }
   return false;
}

int get_order_by_magic_number(int mg){
   for(int x = 0; x < OrdersTotal(); x++){
      OrderSelect(x,SELECT_BY_POS,MODE_TRADES);
      if(OrderMagicNumber() == mg){
         return OrderTicket();
      }
   }
   return 0;
}

void restart(){
   string cookie=NULL,headers;
   char post[],result[];
   int res;
   int timeout=5000; //--- Timeout below 1000 (1 sec.) is not enough for slow Internet connection
   ResetLastError();
   string url = "http://127.0.0.1/restart";
   //Print(url);
   res=WebRequest("GET",url,cookie,NULL,5000,post,0,result,headers);
   
   
   for(int j =0; j< OrdersTotal(); j++){
      OrderSelect(j, SELECT_BY_POS,MODE_TRADES);
      if( OrderType() == OP_BUY ){
         OrderClose(OrderTicket(),1,Bid,0,Red);
      } else {
         OrderClose(OrderTicket(),1,Ask,0,Red);
      }
   }
   
}