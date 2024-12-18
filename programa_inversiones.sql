toc.dat                                                                                             0000600 0004000 0002000 00000115654 14726041174 0014461 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        PGDMP   $        
    
        |           programa_inversiones    17.2    17.2 r    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false         �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false         �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false         �           1262    16384    programa_inversiones    DATABASE     �   CREATE DATABASE programa_inversiones WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Spanish_Chile.1252';
 $   DROP DATABASE programa_inversiones;
                     postgres    false         �            1255    16540    actualizar_plazo()    FUNCTION     �   CREATE FUNCTION public.actualizar_plazo() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.Plazo := DATE_PART('day', NEW.FechaVencimiento - NEW.FechaEmision);
    RETURN NEW;
END;
$$;
 )   DROP FUNCTION public.actualizar_plazo();
       public               postgres    false         �            1255    16579    calcular_rentabilidad()    FUNCTION     �  CREATE FUNCTION public.calcular_rentabilidad() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    precio_promedio NUMERIC;
BEGIN
    -- Obtener el precio promedio de compra de la acción
    SELECT SUM(Cantidad * PrecioUnitario + COALESCE(Comision, 0)) / SUM(Cantidad)
    INTO precio_promedio
    FROM Facturas
    WHERE Tipo = 'Compra' AND NombreActivo = (SELECT Nombre FROM Accion WHERE ID_Accion = NEW.ID_Accion);

    -- Si el precio promedio no se encuentra, asignar rentabilidad como NULL
    IF precio_promedio IS NULL THEN
        NEW.Rentabilidad := NULL;
    ELSE
        -- Calcular la rentabilidad
        NEW.Rentabilidad := ROUND(((NEW.ValorPorAccion / precio_promedio) - 1) * 100, 2);
    END IF;

    RETURN NEW;
END;
$$;
 .   DROP FUNCTION public.calcular_rentabilidad();
       public               postgres    false         �            1255    16556    calcular_valor_factura()    FUNCTION        CREATE FUNCTION public.calcular_valor_factura() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Suma Comision + Gasto
    NEW.Valor := ROUND((NEW.Comision + NEW.Gasto) * 0.19 + NEW.Comision + NEW.Gasto + NEW.SubTotal);
    RETURN NEW;
END;
$$;
 /   DROP FUNCTION public.calcular_valor_factura();
       public               postgres    false         �            1255    16554    update_subtotal()    FUNCTION     �   CREATE FUNCTION public.update_subtotal() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.SubTotal := NEW.Cantidad * NEW.PrecioUnitario;
    RETURN NEW;
END;
$$;
 (   DROP FUNCTION public.update_subtotal();
       public               postgres    false         �            1259    16478    accion    TABLE     
  CREATE TABLE public.accion (
    id_accion integer NOT NULL,
    ticker character varying(15) NOT NULL,
    nombre character varying(100) NOT NULL,
    mercado character varying(50),
    sector character varying(50),
    cantidad numeric(10,2) DEFAULT 0 NOT NULL
);
    DROP TABLE public.accion;
       public         heap r       postgres    false         �            1259    16477    accion_id_accion_seq    SEQUENCE     �   CREATE SEQUENCE public.accion_id_accion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.accion_id_accion_seq;
       public               postgres    false    232         �           0    0    accion_id_accion_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.accion_id_accion_seq OWNED BY public.accion.id_accion;
          public               postgres    false    231         �            1259    16440    boletagarantia    TABLE       CREATE TABLE public.boletagarantia (
    numero integer NOT NULL,
    id_banco integer NOT NULL,
    id_beneficiario integer NOT NULL,
    glosa text,
    vencimiento date NOT NULL,
    moneda character varying(10) NOT NULL,
    monto numeric(15,2) NOT NULL,
    fechaemision date NOT NULL,
    estado character varying(20) DEFAULT 'Activa'::character varying NOT NULL,
    documento character varying(255),
    tomada_por_empresa character varying(255),
    tomada_por_rut character varying(20),
    id_empresa integer
);
 "   DROP TABLE public.boletagarantia;
       public         heap r       postgres    false         �            1259    16439    boletagarantia_numero_seq    SEQUENCE     �   CREATE SEQUENCE public.boletagarantia_numero_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.boletagarantia_numero_seq;
       public               postgres    false    226         �           0    0    boletagarantia_numero_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.boletagarantia_numero_seq OWNED BY public.boletagarantia.numero;
          public               postgres    false    225         �            1259    16499    depositoaplazo    TABLE       CREATE TABLE public.depositoaplazo (
    id_deposito bigint NOT NULL,
    id_entidadcomercial integer NOT NULL,
    id_banco integer NOT NULL,
    fechaemision date NOT NULL,
    fechavencimiento date NOT NULL,
    moneda character varying(10) NOT NULL,
    montoinicial numeric(15,2) NOT NULL,
    montofinal numeric(15,2),
    comprobante character varying(255),
    tipodeposito character varying(20),
    interesganado numeric(15,2) DEFAULT 0.00,
    plazo integer,
    tasainteres numeric(6,4),
    reajusteganado numeric(15,2),
    capitalrenovacion numeric(15,2),
    fechaemisionrenovacion date,
    tasainteresrenovacion numeric(5,2),
    plazorenovacion integer,
    tasaperiodo numeric(5,2),
    fechavencimientorenovacion date,
    totalpagarrenovacion numeric(15,2)
);
 "   DROP TABLE public.depositoaplazo;
       public         heap r       postgres    false         �            1259    16498    depositoaplazo_id_deposito_seq    SEQUENCE     �   CREATE SEQUENCE public.depositoaplazo_id_deposito_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 5   DROP SEQUENCE public.depositoaplazo_id_deposito_seq;
       public               postgres    false    236         �           0    0    depositoaplazo_id_deposito_seq    SEQUENCE OWNED BY     a   ALTER SEQUENCE public.depositoaplazo_id_deposito_seq OWNED BY public.depositoaplazo.id_deposito;
          public               postgres    false    235         �            1259    16487 
   dividendos    TABLE     �  CREATE TABLE public.dividendos (
    id_dividendo integer NOT NULL,
    id_accion integer NOT NULL,
    nombre character varying(255) DEFAULT 'Sin Nombre'::character varying NOT NULL,
    fechacierre date DEFAULT CURRENT_DATE NOT NULL,
    fechapago date DEFAULT CURRENT_DATE NOT NULL,
    valorporaccion numeric(10,2) DEFAULT 0.00 NOT NULL,
    moneda character varying(10) DEFAULT 'CLP'::character varying NOT NULL,
    valortotal numeric(15,2) DEFAULT 0.00,
    rentabilidad numeric(5,2) DEFAULT 0.00
);
    DROP TABLE public.dividendos;
       public         heap r       postgres    false         �            1259    16486    dividendos_id_dividendo_seq    SEQUENCE     �   CREATE SEQUENCE public.dividendos_id_dividendo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.dividendos_id_dividendo_seq;
       public               postgres    false    234         �           0    0    dividendos_id_dividendo_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.dividendos_id_dividendo_seq OWNED BY public.dividendos.id_dividendo;
          public               postgres    false    233         �            1259    16386    entidad    TABLE     0  CREATE TABLE public.entidad (
    id_entidad integer NOT NULL,
    rut character varying(20) NOT NULL,
    nombre character varying(100) NOT NULL,
    tipoentidad character varying(50) NOT NULL,
    email character varying(100),
    fonofijo character varying(15),
    fonomovil character varying(15)
);
    DROP TABLE public.entidad;
       public         heap r       postgres    false         �            1259    16385    entidad_id_entidad_seq    SEQUENCE     �   CREATE SEQUENCE public.entidad_id_entidad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.entidad_id_entidad_seq;
       public               postgres    false    218         �           0    0    entidad_id_entidad_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.entidad_id_entidad_seq OWNED BY public.entidad.id_entidad;
          public               postgres    false    217         �            1259    16395    entidadcomercial    TABLE     9  CREATE TABLE public.entidadcomercial (
    id_entidad integer NOT NULL,
    rut character varying(20) NOT NULL,
    nombre character varying(100) NOT NULL,
    tipoentidad character varying(50) NOT NULL,
    fonofijo character varying(15),
    fonomovil character varying(15),
    email character varying(255)
);
 $   DROP TABLE public.entidadcomercial;
       public         heap r       postgres    false         �            1259    16394    entidadcomercial_id_entidad_seq    SEQUENCE     �   CREATE SEQUENCE public.entidadcomercial_id_entidad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public.entidadcomercial_id_entidad_seq;
       public               postgres    false    220         �           0    0    entidadcomercial_id_entidad_seq    SEQUENCE OWNED BY     c   ALTER SEQUENCE public.entidadcomercial_id_entidad_seq OWNED BY public.entidadcomercial.id_entidad;
          public               postgres    false    219         �            1259    16423    facturas    TABLE     *  CREATE TABLE public.facturas (
    numerofactura integer NOT NULL,
    fecha date NOT NULL,
    tipo character varying(50) NOT NULL,
    cantidad integer NOT NULL,
    valor numeric(15,2) NOT NULL,
    subtotal numeric(15,2) NOT NULL,
    comision numeric(15,2),
    gasto numeric(15,2),
    adjuntofactura character varying(255),
    id_tipoinversion integer NOT NULL,
    preciounitario numeric(15,2),
    nombreactivo character varying(100) NOT NULL,
    tipo_entidad character varying(20),
    id_entidad integer,
    id_entidad_comercial integer
);
    DROP TABLE public.facturas;
       public         heap r       postgres    false         �            1259    16422    facturas_numerofactura_seq    SEQUENCE     �   CREATE SEQUENCE public.facturas_numerofactura_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 1   DROP SEQUENCE public.facturas_numerofactura_seq;
       public               postgres    false    224         �           0    0    facturas_numerofactura_seq    SEQUENCE OWNED BY     Y   ALTER SEQUENCE public.facturas_numerofactura_seq OWNED BY public.facturas.numerofactura;
          public               postgres    false    223         �            1259    16459    fondosmutuos    TABLE     �  CREATE TABLE public.fondosmutuos (
    id_fondo integer NOT NULL,
    nombre character varying(100) NOT NULL,
    montoinvertido numeric(15,2) NOT NULL,
    rentabilidad numeric(5,2),
    montofinal numeric(15,2),
    id_entidad integer NOT NULL,
    comprobante character varying(255),
    tiporiesgo character varying(20),
    fechainicio date,
    fechatermino date,
    id_banco integer
);
     DROP TABLE public.fondosmutuos;
       public         heap r       postgres    false         �            1259    16458    fondosmutuos_id_fondo_seq    SEQUENCE     �   CREATE SEQUENCE public.fondosmutuos_id_fondo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 0   DROP SEQUENCE public.fondosmutuos_id_fondo_seq;
       public               postgres    false    228         �           0    0    fondosmutuos_id_fondo_seq    SEQUENCE OWNED BY     W   ALTER SEQUENCE public.fondosmutuos_id_fondo_seq OWNED BY public.fondosmutuos.id_fondo;
          public               postgres    false    227         �            1259    16582 
   parametros    TABLE     �   CREATE TABLE public.parametros (
    id_parametro integer NOT NULL,
    nombre character varying(255) NOT NULL,
    valor numeric(15,2) NOT NULL,
    fechaactualizacion timestamp(0) without time zone DEFAULT now()
);
    DROP TABLE public.parametros;
       public         heap r       postgres    false         �            1259    16581    parametros_id_parametro_seq    SEQUENCE     �   CREATE SEQUENCE public.parametros_id_parametro_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.parametros_id_parametro_seq;
       public               postgres    false    240         �           0    0    parametros_id_parametro_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.parametros_id_parametro_seq OWNED BY public.parametros.id_parametro;
          public               postgres    false    239         �            1259    16471    polizas    TABLE     �   CREATE TABLE public.polizas (
    numero integer NOT NULL,
    tipoasegurado character varying(50) NOT NULL,
    fechainicio date NOT NULL,
    fechatermino date NOT NULL,
    monto numeric(15,2) NOT NULL,
    adjuntopoliza character varying(255)
);
    DROP TABLE public.polizas;
       public         heap r       postgres    false         �            1259    16470    polizas_numero_seq    SEQUENCE     �   CREATE SEQUENCE public.polizas_numero_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 )   DROP SEQUENCE public.polizas_numero_seq;
       public               postgres    false    230         �           0    0    polizas_numero_seq    SEQUENCE OWNED BY     I   ALTER SEQUENCE public.polizas_numero_seq OWNED BY public.polizas.numero;
          public               postgres    false    229         �            1259    16416    tipoinversion    TABLE     j   CREATE TABLE public.tipoinversion (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);
 !   DROP TABLE public.tipoinversion;
       public         heap r       postgres    false         �            1259    16415    tipoinversion_id_seq    SEQUENCE     �   CREATE SEQUENCE public.tipoinversion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 +   DROP SEQUENCE public.tipoinversion_id_seq;
       public               postgres    false    222         �           0    0    tipoinversion_id_seq    SEQUENCE OWNED BY     M   ALTER SEQUENCE public.tipoinversion_id_seq OWNED BY public.tipoinversion.id;
          public               postgres    false    221         �            1259    16520    usuarios    TABLE     �   CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombreusuario character varying(50) NOT NULL,
    "contraseña" character varying(255) NOT NULL
);
    DROP TABLE public.usuarios;
       public         heap r       postgres    false         �            1259    16519    usuarios_id_seq    SEQUENCE     �   CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 &   DROP SEQUENCE public.usuarios_id_seq;
       public               postgres    false    238         �           0    0    usuarios_id_seq    SEQUENCE OWNED BY     C   ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;
          public               postgres    false    237         �           2604    16481    accion id_accion    DEFAULT     t   ALTER TABLE ONLY public.accion ALTER COLUMN id_accion SET DEFAULT nextval('public.accion_id_accion_seq'::regclass);
 ?   ALTER TABLE public.accion ALTER COLUMN id_accion DROP DEFAULT;
       public               postgres    false    231    232    232         �           2604    16443    boletagarantia numero    DEFAULT     ~   ALTER TABLE ONLY public.boletagarantia ALTER COLUMN numero SET DEFAULT nextval('public.boletagarantia_numero_seq'::regclass);
 D   ALTER TABLE public.boletagarantia ALTER COLUMN numero DROP DEFAULT;
       public               postgres    false    226    225    226         �           2604    16547    depositoaplazo id_deposito    DEFAULT     �   ALTER TABLE ONLY public.depositoaplazo ALTER COLUMN id_deposito SET DEFAULT nextval('public.depositoaplazo_id_deposito_seq'::regclass);
 I   ALTER TABLE public.depositoaplazo ALTER COLUMN id_deposito DROP DEFAULT;
       public               postgres    false    236    235    236         �           2604    16490    dividendos id_dividendo    DEFAULT     �   ALTER TABLE ONLY public.dividendos ALTER COLUMN id_dividendo SET DEFAULT nextval('public.dividendos_id_dividendo_seq'::regclass);
 F   ALTER TABLE public.dividendos ALTER COLUMN id_dividendo DROP DEFAULT;
       public               postgres    false    233    234    234         �           2604    16389    entidad id_entidad    DEFAULT     x   ALTER TABLE ONLY public.entidad ALTER COLUMN id_entidad SET DEFAULT nextval('public.entidad_id_entidad_seq'::regclass);
 A   ALTER TABLE public.entidad ALTER COLUMN id_entidad DROP DEFAULT;
       public               postgres    false    218    217    218         �           2604    16398    entidadcomercial id_entidad    DEFAULT     �   ALTER TABLE ONLY public.entidadcomercial ALTER COLUMN id_entidad SET DEFAULT nextval('public.entidadcomercial_id_entidad_seq'::regclass);
 J   ALTER TABLE public.entidadcomercial ALTER COLUMN id_entidad DROP DEFAULT;
       public               postgres    false    219    220    220         �           2604    16426    facturas numerofactura    DEFAULT     �   ALTER TABLE ONLY public.facturas ALTER COLUMN numerofactura SET DEFAULT nextval('public.facturas_numerofactura_seq'::regclass);
 E   ALTER TABLE public.facturas ALTER COLUMN numerofactura DROP DEFAULT;
       public               postgres    false    224    223    224         �           2604    16462    fondosmutuos id_fondo    DEFAULT     ~   ALTER TABLE ONLY public.fondosmutuos ALTER COLUMN id_fondo SET DEFAULT nextval('public.fondosmutuos_id_fondo_seq'::regclass);
 D   ALTER TABLE public.fondosmutuos ALTER COLUMN id_fondo DROP DEFAULT;
       public               postgres    false    228    227    228         �           2604    16585    parametros id_parametro    DEFAULT     �   ALTER TABLE ONLY public.parametros ALTER COLUMN id_parametro SET DEFAULT nextval('public.parametros_id_parametro_seq'::regclass);
 F   ALTER TABLE public.parametros ALTER COLUMN id_parametro DROP DEFAULT;
       public               postgres    false    239    240    240         �           2604    16474    polizas numero    DEFAULT     p   ALTER TABLE ONLY public.polizas ALTER COLUMN numero SET DEFAULT nextval('public.polizas_numero_seq'::regclass);
 =   ALTER TABLE public.polizas ALTER COLUMN numero DROP DEFAULT;
       public               postgres    false    229    230    230         �           2604    16419    tipoinversion id    DEFAULT     t   ALTER TABLE ONLY public.tipoinversion ALTER COLUMN id SET DEFAULT nextval('public.tipoinversion_id_seq'::regclass);
 ?   ALTER TABLE public.tipoinversion ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    221    222    222         �           2604    16523    usuarios id    DEFAULT     j   ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);
 :   ALTER TABLE public.usuarios ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    238    237    238         |          0    16478    accion 
   TABLE DATA           V   COPY public.accion (id_accion, ticker, nombre, mercado, sector, cantidad) FROM stdin;
    public               postgres    false    232       4988.dat v          0    16440    boletagarantia 
   TABLE DATA           �   COPY public.boletagarantia (numero, id_banco, id_beneficiario, glosa, vencimiento, moneda, monto, fechaemision, estado, documento, tomada_por_empresa, tomada_por_rut, id_empresa) FROM stdin;
    public               postgres    false    226       4982.dat �          0    16499    depositoaplazo 
   TABLE DATA           v  COPY public.depositoaplazo (id_deposito, id_entidadcomercial, id_banco, fechaemision, fechavencimiento, moneda, montoinicial, montofinal, comprobante, tipodeposito, interesganado, plazo, tasainteres, reajusteganado, capitalrenovacion, fechaemisionrenovacion, tasainteresrenovacion, plazorenovacion, tasaperiodo, fechavencimientorenovacion, totalpagarrenovacion) FROM stdin;
    public               postgres    false    236       4992.dat ~          0    16487 
   dividendos 
   TABLE DATA           �   COPY public.dividendos (id_dividendo, id_accion, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal, rentabilidad) FROM stdin;
    public               postgres    false    234       4990.dat n          0    16386    entidad 
   TABLE DATA           c   COPY public.entidad (id_entidad, rut, nombre, tipoentidad, email, fonofijo, fonomovil) FROM stdin;
    public               postgres    false    218       4974.dat p          0    16395    entidadcomercial 
   TABLE DATA           l   COPY public.entidadcomercial (id_entidad, rut, nombre, tipoentidad, fonofijo, fonomovil, email) FROM stdin;
    public               postgres    false    220       4976.dat t          0    16423    facturas 
   TABLE DATA           �   COPY public.facturas (numerofactura, fecha, tipo, cantidad, valor, subtotal, comision, gasto, adjuntofactura, id_tipoinversion, preciounitario, nombreactivo, tipo_entidad, id_entidad, id_entidad_comercial) FROM stdin;
    public               postgres    false    224       4980.dat x          0    16459    fondosmutuos 
   TABLE DATA           �   COPY public.fondosmutuos (id_fondo, nombre, montoinvertido, rentabilidad, montofinal, id_entidad, comprobante, tiporiesgo, fechainicio, fechatermino, id_banco) FROM stdin;
    public               postgres    false    228       4984.dat �          0    16582 
   parametros 
   TABLE DATA           U   COPY public.parametros (id_parametro, nombre, valor, fechaactualizacion) FROM stdin;
    public               postgres    false    240       4996.dat z          0    16471    polizas 
   TABLE DATA           i   COPY public.polizas (numero, tipoasegurado, fechainicio, fechatermino, monto, adjuntopoliza) FROM stdin;
    public               postgres    false    230       4986.dat r          0    16416    tipoinversion 
   TABLE DATA           3   COPY public.tipoinversion (id, nombre) FROM stdin;
    public               postgres    false    222       4978.dat �          0    16520    usuarios 
   TABLE DATA           D   COPY public.usuarios (id, nombreusuario, "contraseña") FROM stdin;
    public               postgres    false    238       4994.dat �           0    0    accion_id_accion_seq    SEQUENCE SET     C   SELECT pg_catalog.setval('public.accion_id_accion_seq', 1, false);
          public               postgres    false    231         �           0    0    boletagarantia_numero_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.boletagarantia_numero_seq', 2, true);
          public               postgres    false    225         �           0    0    depositoaplazo_id_deposito_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.depositoaplazo_id_deposito_seq', 4, true);
          public               postgres    false    235         �           0    0    dividendos_id_dividendo_seq    SEQUENCE SET     I   SELECT pg_catalog.setval('public.dividendos_id_dividendo_seq', 8, true);
          public               postgres    false    233         �           0    0    entidad_id_entidad_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.entidad_id_entidad_seq', 39, true);
          public               postgres    false    217         �           0    0    entidadcomercial_id_entidad_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public.entidadcomercial_id_entidad_seq', 38, true);
          public               postgres    false    219         �           0    0    facturas_numerofactura_seq    SEQUENCE SET     I   SELECT pg_catalog.setval('public.facturas_numerofactura_seq', 1, false);
          public               postgres    false    223         �           0    0    fondosmutuos_id_fondo_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.fondosmutuos_id_fondo_seq', 18, true);
          public               postgres    false    227         �           0    0    parametros_id_parametro_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.parametros_id_parametro_seq', 12, true);
          public               postgres    false    239         �           0    0    polizas_numero_seq    SEQUENCE SET     A   SELECT pg_catalog.setval('public.polizas_numero_seq', 1, false);
          public               postgres    false    229         �           0    0    tipoinversion_id_seq    SEQUENCE SET     B   SELECT pg_catalog.setval('public.tipoinversion_id_seq', 2, true);
          public               postgres    false    221         �           0    0    usuarios_id_seq    SEQUENCE SET     =   SELECT pg_catalog.setval('public.usuarios_id_seq', 1, true);
          public               postgres    false    237         �           2606    16483    accion accion_pkey 
   CONSTRAINT     W   ALTER TABLE ONLY public.accion
    ADD CONSTRAINT accion_pkey PRIMARY KEY (id_accion);
 <   ALTER TABLE ONLY public.accion DROP CONSTRAINT accion_pkey;
       public                 postgres    false    232         �           2606    16485    accion accion_ticker_key 
   CONSTRAINT     U   ALTER TABLE ONLY public.accion
    ADD CONSTRAINT accion_ticker_key UNIQUE (ticker);
 B   ALTER TABLE ONLY public.accion DROP CONSTRAINT accion_ticker_key;
       public                 postgres    false    232         �           2606    16447 "   boletagarantia boletagarantia_pkey 
   CONSTRAINT     d   ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_pkey PRIMARY KEY (numero);
 L   ALTER TABLE ONLY public.boletagarantia DROP CONSTRAINT boletagarantia_pkey;
       public                 postgres    false    226         �           2606    16549 "   depositoaplazo depositoaplazo_pkey 
   CONSTRAINT     i   ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_pkey PRIMARY KEY (id_deposito);
 L   ALTER TABLE ONLY public.depositoaplazo DROP CONSTRAINT depositoaplazo_pkey;
       public                 postgres    false    236         �           2606    16492    dividendos dividendos_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT dividendos_pkey PRIMARY KEY (id_dividendo);
 D   ALTER TABLE ONLY public.dividendos DROP CONSTRAINT dividendos_pkey;
       public                 postgres    false    234         �           2606    16391    entidad entidad_pkey 
   CONSTRAINT     Z   ALTER TABLE ONLY public.entidad
    ADD CONSTRAINT entidad_pkey PRIMARY KEY (id_entidad);
 >   ALTER TABLE ONLY public.entidad DROP CONSTRAINT entidad_pkey;
       public                 postgres    false    218         �           2606    16393    entidad entidad_rut_key 
   CONSTRAINT     Q   ALTER TABLE ONLY public.entidad
    ADD CONSTRAINT entidad_rut_key UNIQUE (rut);
 A   ALTER TABLE ONLY public.entidad DROP CONSTRAINT entidad_rut_key;
       public                 postgres    false    218         �           2606    16400 &   entidadcomercial entidadcomercial_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.entidadcomercial
    ADD CONSTRAINT entidadcomercial_pkey PRIMARY KEY (id_entidad);
 P   ALTER TABLE ONLY public.entidadcomercial DROP CONSTRAINT entidadcomercial_pkey;
       public                 postgres    false    220         �           2606    16402 )   entidadcomercial entidadcomercial_rut_key 
   CONSTRAINT     c   ALTER TABLE ONLY public.entidadcomercial
    ADD CONSTRAINT entidadcomercial_rut_key UNIQUE (rut);
 S   ALTER TABLE ONLY public.entidadcomercial DROP CONSTRAINT entidadcomercial_rut_key;
       public                 postgres    false    220         �           2606    16428    facturas facturas_pkey 
   CONSTRAINT     _   ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_pkey PRIMARY KEY (numerofactura);
 @   ALTER TABLE ONLY public.facturas DROP CONSTRAINT facturas_pkey;
       public                 postgres    false    224         �           2606    16464    fondosmutuos fondosmutuos_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_pkey PRIMARY KEY (id_fondo);
 H   ALTER TABLE ONLY public.fondosmutuos DROP CONSTRAINT fondosmutuos_pkey;
       public                 postgres    false    228         �           2606    16590     parametros parametros_nombre_key 
   CONSTRAINT     ]   ALTER TABLE ONLY public.parametros
    ADD CONSTRAINT parametros_nombre_key UNIQUE (nombre);
 J   ALTER TABLE ONLY public.parametros DROP CONSTRAINT parametros_nombre_key;
       public                 postgres    false    240         �           2606    16588    parametros parametros_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.parametros
    ADD CONSTRAINT parametros_pkey PRIMARY KEY (id_parametro);
 D   ALTER TABLE ONLY public.parametros DROP CONSTRAINT parametros_pkey;
       public                 postgres    false    240         �           2606    16476    polizas polizas_pkey 
   CONSTRAINT     V   ALTER TABLE ONLY public.polizas
    ADD CONSTRAINT polizas_pkey PRIMARY KEY (numero);
 >   ALTER TABLE ONLY public.polizas DROP CONSTRAINT polizas_pkey;
       public                 postgres    false    230         �           2606    16421     tipoinversion tipoinversion_pkey 
   CONSTRAINT     ^   ALTER TABLE ONLY public.tipoinversion
    ADD CONSTRAINT tipoinversion_pkey PRIMARY KEY (id);
 J   ALTER TABLE ONLY public.tipoinversion DROP CONSTRAINT tipoinversion_pkey;
       public                 postgres    false    222         �           2606    16527 #   usuarios usuarios_nombreusuario_key 
   CONSTRAINT     g   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_nombreusuario_key UNIQUE (nombreusuario);
 M   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_nombreusuario_key;
       public                 postgres    false    238         �           2606    16525    usuarios usuarios_pkey 
   CONSTRAINT     T   ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);
 @   ALTER TABLE ONLY public.usuarios DROP CONSTRAINT usuarios_pkey;
       public                 postgres    false    238         �           2620    16555    facturas before_update_facturas    TRIGGER     �   CREATE TRIGGER before_update_facturas BEFORE INSERT OR UPDATE ON public.facturas FOR EACH ROW EXECUTE FUNCTION public.update_subtotal();
 8   DROP TRIGGER before_update_facturas ON public.facturas;
       public               postgres    false    242    224         �           2620    16541 '   depositoaplazo trigger_actualizar_plazo    TRIGGER     �   CREATE TRIGGER trigger_actualizar_plazo BEFORE INSERT OR UPDATE ON public.depositoaplazo FOR EACH ROW EXECUTE FUNCTION public.actualizar_plazo();

ALTER TABLE public.depositoaplazo DISABLE TRIGGER trigger_actualizar_plazo;
 @   DROP TRIGGER trigger_actualizar_plazo ON public.depositoaplazo;
       public               postgres    false    236    241         �           2620    16580 (   dividendos trigger_calcular_rentabilidad    TRIGGER     �   CREATE TRIGGER trigger_calcular_rentabilidad BEFORE INSERT OR UPDATE ON public.dividendos FOR EACH ROW EXECUTE FUNCTION public.calcular_rentabilidad();
 A   DROP TRIGGER trigger_calcular_rentabilidad ON public.dividendos;
       public               postgres    false    234    244         �           2620    16557    facturas trigger_calcular_valor    TRIGGER     �   CREATE TRIGGER trigger_calcular_valor BEFORE INSERT OR UPDATE ON public.facturas FOR EACH ROW EXECUTE FUNCTION public.calcular_valor_factura();
 8   DROP TRIGGER trigger_calcular_valor ON public.facturas;
       public               postgres    false    243    224         �           2606    16448 +   boletagarantia boletagarantia_id_banco_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);
 U   ALTER TABLE ONLY public.boletagarantia DROP CONSTRAINT boletagarantia_id_banco_fkey;
       public               postgres    false    4778    218    226         �           2606    16453 -   boletagarantia boletagarantia_id_cliente_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_id_cliente_fkey FOREIGN KEY (id_beneficiario) REFERENCES public.entidadcomercial(id_entidad);
 W   ALTER TABLE ONLY public.boletagarantia DROP CONSTRAINT boletagarantia_id_cliente_fkey;
       public               postgres    false    220    226    4782         �           2606    16510 +   depositoaplazo depositoaplazo_id_banco_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);
 U   ALTER TABLE ONLY public.depositoaplazo DROP CONSTRAINT depositoaplazo_id_banco_fkey;
       public               postgres    false    218    4778    236         �           2606    16505 -   depositoaplazo depositoaplazo_id_empresa_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_id_empresa_fkey FOREIGN KEY (id_entidadcomercial) REFERENCES public.entidadcomercial(id_entidad);
 W   ALTER TABLE ONLY public.depositoaplazo DROP CONSTRAINT depositoaplazo_id_empresa_fkey;
       public               postgres    false    4782    236    220         �           2606    16493 $   dividendos dividendos_id_accion_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT dividendos_id_accion_fkey FOREIGN KEY (id_accion) REFERENCES public.accion(id_accion);
 N   ALTER TABLE ONLY public.dividendos DROP CONSTRAINT dividendos_id_accion_fkey;
       public               postgres    false    234    232    4796         �           2606    16617 (   facturas facturas_entidad_comercial_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_entidad_comercial_fkey FOREIGN KEY (id_entidad_comercial) REFERENCES public.entidadcomercial(id_entidad) ON DELETE CASCADE;
 R   ALTER TABLE ONLY public.facturas DROP CONSTRAINT facturas_entidad_comercial_fkey;
       public               postgres    false    220    224    4782         �           2606    16612    facturas facturas_entidad_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_entidad_fkey FOREIGN KEY (id_entidad) REFERENCES public.entidad(id_entidad) ON DELETE CASCADE;
 H   ALTER TABLE ONLY public.facturas DROP CONSTRAINT facturas_entidad_fkey;
       public               postgres    false    4778    224    218         �           2606    16434 '   facturas facturas_id_tipoinversion_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_id_tipoinversion_fkey FOREIGN KEY (id_tipoinversion) REFERENCES public.tipoinversion(id);
 Q   ALTER TABLE ONLY public.facturas DROP CONSTRAINT facturas_id_tipoinversion_fkey;
       public               postgres    false    224    4786    222         �           2606    16572    dividendos fk_accion    FK CONSTRAINT     }   ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT fk_accion FOREIGN KEY (id_accion) REFERENCES public.accion(id_accion);
 >   ALTER TABLE ONLY public.dividendos DROP CONSTRAINT fk_accion;
       public               postgres    false    234    232    4796         �           2606    16622     boletagarantia fk_boleta_empresa    FK CONSTRAINT     �   ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT fk_boleta_empresa FOREIGN KEY (id_empresa) REFERENCES public.entidadcomercial(id_entidad);
 J   ALTER TABLE ONLY public.boletagarantia DROP CONSTRAINT fk_boleta_empresa;
       public               postgres    false    220    226    4782         �           2606    16542 .   depositoaplazo fk_deposito_id_entidadcomercial    FK CONSTRAINT     �   ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT fk_deposito_id_entidadcomercial FOREIGN KEY (id_entidadcomercial) REFERENCES public.entidadcomercial(id_entidad);
 X   ALTER TABLE ONLY public.depositoaplazo DROP CONSTRAINT fk_deposito_id_entidadcomercial;
       public               postgres    false    4782    220    236         �           2606    16528 '   fondosmutuos fondosmutuos_id_banco_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);
 Q   ALTER TABLE ONLY public.fondosmutuos DROP CONSTRAINT fondosmutuos_id_banco_fkey;
       public               postgres    false    228    218    4778         �           2606    16533 2   fondosmutuos fondosmutuos_id_entidadcomercial_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_id_entidadcomercial_fkey FOREIGN KEY (id_entidad) REFERENCES public.entidadcomercial(id_entidad);
 \   ALTER TABLE ONLY public.fondosmutuos DROP CONSTRAINT fondosmutuos_id_entidadcomercial_fkey;
       public               postgres    false    228    4782    220                                                                                            4988.dat                                                                                            0000600 0004000 0002000 00000000177 14726041174 0014301 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1961295	N/A_1961295	CRUZADOS	\N	\N	8048.00
54321	N/A_54321	FALABELLA	\N	\N	200.00
12345678	N/A_12345678	SAN	\N	\N	1069.00
\.


                                                                                                                                                                                                                                                                                                                                                                                                 4982.dat                                                                                            0000600 0004000 0002000 00000000166 14726041174 0014271 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        416118	37	25	olas	2024-01-01	CLP	900000.00	2025-01-01	Vigente	static\\uploads\\boleta_garantiaTest1.pdf	\N	\N	25
\.


                                                                                                                                                                                                                                                                                                                                                                                                          4992.dat                                                                                            0000600 0004000 0002000 00000000301 14726041174 0014261 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1002	26	38	2024-11-02	2025-11-02	CLP	900000.00	\N	static\\uploads\\deposito_a_plazoTest3_-_copia.pdf	Renovable	5000.00	\N	3.5000	\N	900000.00	2024-11-02	3.70	365	3.70	2024-11-02	912400.00
\.


                                                                                                                                                                                                                                                                                                                               4990.dat                                                                                            0000600 0004000 0002000 00000000136 14726041174 0014265 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        7	1961295	DIVIDENDO TRIMESTRAL Q5 2024	2024-05-15	2025-01-12	200.00	USD	1609600.00	14.38
\.


                                                                                                                                                                                                                                                                                                                                                                                                                                  4974.dat                                                                                            0000600 0004000 0002000 00000001064 14726041174 0014270 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        33	172345678	BANCO ESTRELLA S.A.	Banco	andres.martinez@bancoestrella.com	234567890	987654321
34	156781234	MATÍAS FERNÁNDEZ ORELLANA	Corredor	matias.fernandez@corredoresfinancieros.cl	234567890	987654321
35	923456781	ASEGURADORA GLOBAL S.A.	Compania	contacto@aseguradoraglobal.com	234567890	998765432
36	764287908	ITAU CORREDORES DE BOLSA LTDA.	Corredor	corredoradebolsa@itau.cl	226860888	6006860888
37	765432108	BANCO FINANCIERO DEL SUR	Banco	\N	\N	\N
38	754321096	BANCO DEL HORIZONTE S.A.	Banco	\N	\N	\N
39	785432109	BANCO DEL PROGRESO S.A.	Banco	\N	\N	\N
\.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                            4976.dat                                                                                            0000600 0004000 0002000 00000000663 14726041174 0014276 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        23	834567890	SOLUCIONES EMPRESARIALES S.A.	Empresa	223456789	987654321	contacto@solucionesempresariales.cl
24	198765432	CAROLINA MUÑOZ TORRES	Cliente	245678901	976543210	carolina.munoz@clientesficticios.cl
25	812345679	SOLUCIONES GLOBALES S.A.	Empresa	\N	\N	\N
26	985749633	INNOVACIÓN EMPRESARIAL LTDA.	Empresa	\N	\N	\N
28	192345674	MARÍA JOSÉ GUTIÉRREZ	Cliente	\N	\N	\N
38	219876543	SEBASTIÁN ARAYA LÓPEZ	Cliente	\N	\N	\N
\.


                                                                             4980.dat                                                                                            0000600 0004000 0002000 00000000212 14726041174 0014257 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1961292	2019-11-17	Compra	8042	1205047.00	1194237.00	4182.00	4902.00	static/uploads/factura_test.pdf	1	148.50	CRUZADOS	Entidad	36	\N
\.


                                                                                                                                                                                                                                                                                                                                                                                      4984.dat                                                                                            0000600 0004000 0002000 00000000311 14726041174 0014263 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        18	FONDO RENTA FIJA CLP	900000.00	\N	1300000.00	23	C:/Users/BBF_Informatica/Desktop/visual-code/gitClones/proyecto_inversionesV3/static/uploads/fondo_mutuo_test2.pdf	Bajo	2024-01-01	2025-01-01	37
\.


                                                                                                                                                                                                                                                                                                                       4996.dat                                                                                            0000600 0004000 0002000 00000000157 14726041174 0014276 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1	Dolar	970.91	2024-12-06 08:29:12
11	Euro	1023.88	2024-12-06 08:54:52
12	UF	38324.11	2024-12-06 09:00:16
\.


                                                                                                                                                                                                                                                                                                                                                                                                                 4986.dat                                                                                            0000600 0004000 0002000 00000000005 14726041174 0014265 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        \.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           4978.dat                                                                                            0000600 0004000 0002000 00000000026 14726041174 0014271 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1	Compra
2	Venta
\.


                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          4994.dat                                                                                            0000600 0004000 0002000 00000000260 14726041174 0014267 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        1	admin	scrypt:32768:8:1$a9xceycXX5B9oyRw$28aca242c210f02798db2d66e85fe147f8b7ac9e3b63e53f6862dd409bc1783cd03e69a1c7e8594eca1907beee2d3372745c34b05f1430f3d20d36057b53fbc3
\.


                                                                                                                                                                                                                                                                                                                                                restore.sql                                                                                         0000600 0004000 0002000 00000076671 14726041174 0015413 0                                                                                                    ustar 00postgres                        postgres                        0000000 0000000                                                                                                                                                                        --
-- NOTE:
--
-- File paths need to be edited. Search for $$PATH$$ and
-- replace it with the path to the directory containing
-- the extracted data files.
--
--
-- PostgreSQL database dump
--

-- Dumped from database version 17.2
-- Dumped by pg_dump version 17.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE programa_inversiones;
--
-- Name: programa_inversiones; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE programa_inversiones WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Spanish_Chile.1252';


ALTER DATABASE programa_inversiones OWNER TO postgres;

\connect programa_inversiones

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: actualizar_plazo(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.actualizar_plazo() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.Plazo := DATE_PART('day', NEW.FechaVencimiento - NEW.FechaEmision);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.actualizar_plazo() OWNER TO postgres;

--
-- Name: calcular_rentabilidad(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_rentabilidad() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    precio_promedio NUMERIC;
BEGIN
    -- Obtener el precio promedio de compra de la acción
    SELECT SUM(Cantidad * PrecioUnitario + COALESCE(Comision, 0)) / SUM(Cantidad)
    INTO precio_promedio
    FROM Facturas
    WHERE Tipo = 'Compra' AND NombreActivo = (SELECT Nombre FROM Accion WHERE ID_Accion = NEW.ID_Accion);

    -- Si el precio promedio no se encuentra, asignar rentabilidad como NULL
    IF precio_promedio IS NULL THEN
        NEW.Rentabilidad := NULL;
    ELSE
        -- Calcular la rentabilidad
        NEW.Rentabilidad := ROUND(((NEW.ValorPorAccion / precio_promedio) - 1) * 100, 2);
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.calcular_rentabilidad() OWNER TO postgres;

--
-- Name: calcular_valor_factura(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calcular_valor_factura() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Suma Comision + Gasto
    NEW.Valor := ROUND((NEW.Comision + NEW.Gasto) * 0.19 + NEW.Comision + NEW.Gasto + NEW.SubTotal);
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.calcular_valor_factura() OWNER TO postgres;

--
-- Name: update_subtotal(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_subtotal() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.SubTotal := NEW.Cantidad * NEW.PrecioUnitario;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_subtotal() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accion (
    id_accion integer NOT NULL,
    ticker character varying(15) NOT NULL,
    nombre character varying(100) NOT NULL,
    mercado character varying(50),
    sector character varying(50),
    cantidad numeric(10,2) DEFAULT 0 NOT NULL
);


ALTER TABLE public.accion OWNER TO postgres;

--
-- Name: accion_id_accion_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.accion_id_accion_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.accion_id_accion_seq OWNER TO postgres;

--
-- Name: accion_id_accion_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.accion_id_accion_seq OWNED BY public.accion.id_accion;


--
-- Name: boletagarantia; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.boletagarantia (
    numero integer NOT NULL,
    id_banco integer NOT NULL,
    id_beneficiario integer NOT NULL,
    glosa text,
    vencimiento date NOT NULL,
    moneda character varying(10) NOT NULL,
    monto numeric(15,2) NOT NULL,
    fechaemision date NOT NULL,
    estado character varying(20) DEFAULT 'Activa'::character varying NOT NULL,
    documento character varying(255),
    tomada_por_empresa character varying(255),
    tomada_por_rut character varying(20),
    id_empresa integer
);


ALTER TABLE public.boletagarantia OWNER TO postgres;

--
-- Name: boletagarantia_numero_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.boletagarantia_numero_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.boletagarantia_numero_seq OWNER TO postgres;

--
-- Name: boletagarantia_numero_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.boletagarantia_numero_seq OWNED BY public.boletagarantia.numero;


--
-- Name: depositoaplazo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.depositoaplazo (
    id_deposito bigint NOT NULL,
    id_entidadcomercial integer NOT NULL,
    id_banco integer NOT NULL,
    fechaemision date NOT NULL,
    fechavencimiento date NOT NULL,
    moneda character varying(10) NOT NULL,
    montoinicial numeric(15,2) NOT NULL,
    montofinal numeric(15,2),
    comprobante character varying(255),
    tipodeposito character varying(20),
    interesganado numeric(15,2) DEFAULT 0.00,
    plazo integer,
    tasainteres numeric(6,4),
    reajusteganado numeric(15,2),
    capitalrenovacion numeric(15,2),
    fechaemisionrenovacion date,
    tasainteresrenovacion numeric(5,2),
    plazorenovacion integer,
    tasaperiodo numeric(5,2),
    fechavencimientorenovacion date,
    totalpagarrenovacion numeric(15,2)
);


ALTER TABLE public.depositoaplazo OWNER TO postgres;

--
-- Name: depositoaplazo_id_deposito_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.depositoaplazo_id_deposito_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.depositoaplazo_id_deposito_seq OWNER TO postgres;

--
-- Name: depositoaplazo_id_deposito_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.depositoaplazo_id_deposito_seq OWNED BY public.depositoaplazo.id_deposito;


--
-- Name: dividendos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dividendos (
    id_dividendo integer NOT NULL,
    id_accion integer NOT NULL,
    nombre character varying(255) DEFAULT 'Sin Nombre'::character varying NOT NULL,
    fechacierre date DEFAULT CURRENT_DATE NOT NULL,
    fechapago date DEFAULT CURRENT_DATE NOT NULL,
    valorporaccion numeric(10,2) DEFAULT 0.00 NOT NULL,
    moneda character varying(10) DEFAULT 'CLP'::character varying NOT NULL,
    valortotal numeric(15,2) DEFAULT 0.00,
    rentabilidad numeric(5,2) DEFAULT 0.00
);


ALTER TABLE public.dividendos OWNER TO postgres;

--
-- Name: dividendos_id_dividendo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dividendos_id_dividendo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dividendos_id_dividendo_seq OWNER TO postgres;

--
-- Name: dividendos_id_dividendo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dividendos_id_dividendo_seq OWNED BY public.dividendos.id_dividendo;


--
-- Name: entidad; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entidad (
    id_entidad integer NOT NULL,
    rut character varying(20) NOT NULL,
    nombre character varying(100) NOT NULL,
    tipoentidad character varying(50) NOT NULL,
    email character varying(100),
    fonofijo character varying(15),
    fonomovil character varying(15)
);


ALTER TABLE public.entidad OWNER TO postgres;

--
-- Name: entidad_id_entidad_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.entidad_id_entidad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entidad_id_entidad_seq OWNER TO postgres;

--
-- Name: entidad_id_entidad_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.entidad_id_entidad_seq OWNED BY public.entidad.id_entidad;


--
-- Name: entidadcomercial; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entidadcomercial (
    id_entidad integer NOT NULL,
    rut character varying(20) NOT NULL,
    nombre character varying(100) NOT NULL,
    tipoentidad character varying(50) NOT NULL,
    fonofijo character varying(15),
    fonomovil character varying(15),
    email character varying(255)
);


ALTER TABLE public.entidadcomercial OWNER TO postgres;

--
-- Name: entidadcomercial_id_entidad_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.entidadcomercial_id_entidad_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.entidadcomercial_id_entidad_seq OWNER TO postgres;

--
-- Name: entidadcomercial_id_entidad_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.entidadcomercial_id_entidad_seq OWNED BY public.entidadcomercial.id_entidad;


--
-- Name: facturas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.facturas (
    numerofactura integer NOT NULL,
    fecha date NOT NULL,
    tipo character varying(50) NOT NULL,
    cantidad integer NOT NULL,
    valor numeric(15,2) NOT NULL,
    subtotal numeric(15,2) NOT NULL,
    comision numeric(15,2),
    gasto numeric(15,2),
    adjuntofactura character varying(255),
    id_tipoinversion integer NOT NULL,
    preciounitario numeric(15,2),
    nombreactivo character varying(100) NOT NULL,
    tipo_entidad character varying(20),
    id_entidad integer,
    id_entidad_comercial integer
);


ALTER TABLE public.facturas OWNER TO postgres;

--
-- Name: facturas_numerofactura_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.facturas_numerofactura_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.facturas_numerofactura_seq OWNER TO postgres;

--
-- Name: facturas_numerofactura_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.facturas_numerofactura_seq OWNED BY public.facturas.numerofactura;


--
-- Name: fondosmutuos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fondosmutuos (
    id_fondo integer NOT NULL,
    nombre character varying(100) NOT NULL,
    montoinvertido numeric(15,2) NOT NULL,
    rentabilidad numeric(5,2),
    montofinal numeric(15,2),
    id_entidad integer NOT NULL,
    comprobante character varying(255),
    tiporiesgo character varying(20),
    fechainicio date,
    fechatermino date,
    id_banco integer
);


ALTER TABLE public.fondosmutuos OWNER TO postgres;

--
-- Name: fondosmutuos_id_fondo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fondosmutuos_id_fondo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fondosmutuos_id_fondo_seq OWNER TO postgres;

--
-- Name: fondosmutuos_id_fondo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fondosmutuos_id_fondo_seq OWNED BY public.fondosmutuos.id_fondo;


--
-- Name: parametros; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parametros (
    id_parametro integer NOT NULL,
    nombre character varying(255) NOT NULL,
    valor numeric(15,2) NOT NULL,
    fechaactualizacion timestamp(0) without time zone DEFAULT now()
);


ALTER TABLE public.parametros OWNER TO postgres;

--
-- Name: parametros_id_parametro_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.parametros_id_parametro_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.parametros_id_parametro_seq OWNER TO postgres;

--
-- Name: parametros_id_parametro_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.parametros_id_parametro_seq OWNED BY public.parametros.id_parametro;


--
-- Name: polizas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.polizas (
    numero integer NOT NULL,
    tipoasegurado character varying(50) NOT NULL,
    fechainicio date NOT NULL,
    fechatermino date NOT NULL,
    monto numeric(15,2) NOT NULL,
    adjuntopoliza character varying(255)
);


ALTER TABLE public.polizas OWNER TO postgres;

--
-- Name: polizas_numero_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.polizas_numero_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.polizas_numero_seq OWNER TO postgres;

--
-- Name: polizas_numero_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.polizas_numero_seq OWNED BY public.polizas.numero;


--
-- Name: tipoinversion; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tipoinversion (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);


ALTER TABLE public.tipoinversion OWNER TO postgres;

--
-- Name: tipoinversion_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tipoinversion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tipoinversion_id_seq OWNER TO postgres;

--
-- Name: tipoinversion_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tipoinversion_id_seq OWNED BY public.tipoinversion.id;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    nombreusuario character varying(50) NOT NULL,
    "contraseña" character varying(255) NOT NULL
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_seq OWNER TO postgres;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: accion id_accion; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accion ALTER COLUMN id_accion SET DEFAULT nextval('public.accion_id_accion_seq'::regclass);


--
-- Name: boletagarantia numero; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boletagarantia ALTER COLUMN numero SET DEFAULT nextval('public.boletagarantia_numero_seq'::regclass);


--
-- Name: depositoaplazo id_deposito; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.depositoaplazo ALTER COLUMN id_deposito SET DEFAULT nextval('public.depositoaplazo_id_deposito_seq'::regclass);


--
-- Name: dividendos id_dividendo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dividendos ALTER COLUMN id_dividendo SET DEFAULT nextval('public.dividendos_id_dividendo_seq'::regclass);


--
-- Name: entidad id_entidad; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidad ALTER COLUMN id_entidad SET DEFAULT nextval('public.entidad_id_entidad_seq'::regclass);


--
-- Name: entidadcomercial id_entidad; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidadcomercial ALTER COLUMN id_entidad SET DEFAULT nextval('public.entidadcomercial_id_entidad_seq'::regclass);


--
-- Name: facturas numerofactura; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas ALTER COLUMN numerofactura SET DEFAULT nextval('public.facturas_numerofactura_seq'::regclass);


--
-- Name: fondosmutuos id_fondo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fondosmutuos ALTER COLUMN id_fondo SET DEFAULT nextval('public.fondosmutuos_id_fondo_seq'::regclass);


--
-- Name: parametros id_parametro; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametros ALTER COLUMN id_parametro SET DEFAULT nextval('public.parametros_id_parametro_seq'::regclass);


--
-- Name: polizas numero; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polizas ALTER COLUMN numero SET DEFAULT nextval('public.polizas_numero_seq'::regclass);


--
-- Name: tipoinversion id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipoinversion ALTER COLUMN id SET DEFAULT nextval('public.tipoinversion_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Data for Name: accion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accion (id_accion, ticker, nombre, mercado, sector, cantidad) FROM stdin;
\.
COPY public.accion (id_accion, ticker, nombre, mercado, sector, cantidad) FROM '$$PATH$$/4988.dat';

--
-- Data for Name: boletagarantia; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.boletagarantia (numero, id_banco, id_beneficiario, glosa, vencimiento, moneda, monto, fechaemision, estado, documento, tomada_por_empresa, tomada_por_rut, id_empresa) FROM stdin;
\.
COPY public.boletagarantia (numero, id_banco, id_beneficiario, glosa, vencimiento, moneda, monto, fechaemision, estado, documento, tomada_por_empresa, tomada_por_rut, id_empresa) FROM '$$PATH$$/4982.dat';

--
-- Data for Name: depositoaplazo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.depositoaplazo (id_deposito, id_entidadcomercial, id_banco, fechaemision, fechavencimiento, moneda, montoinicial, montofinal, comprobante, tipodeposito, interesganado, plazo, tasainteres, reajusteganado, capitalrenovacion, fechaemisionrenovacion, tasainteresrenovacion, plazorenovacion, tasaperiodo, fechavencimientorenovacion, totalpagarrenovacion) FROM stdin;
\.
COPY public.depositoaplazo (id_deposito, id_entidadcomercial, id_banco, fechaemision, fechavencimiento, moneda, montoinicial, montofinal, comprobante, tipodeposito, interesganado, plazo, tasainteres, reajusteganado, capitalrenovacion, fechaemisionrenovacion, tasainteresrenovacion, plazorenovacion, tasaperiodo, fechavencimientorenovacion, totalpagarrenovacion) FROM '$$PATH$$/4992.dat';

--
-- Data for Name: dividendos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dividendos (id_dividendo, id_accion, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal, rentabilidad) FROM stdin;
\.
COPY public.dividendos (id_dividendo, id_accion, nombre, fechacierre, fechapago, valorporaccion, moneda, valortotal, rentabilidad) FROM '$$PATH$$/4990.dat';

--
-- Data for Name: entidad; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.entidad (id_entidad, rut, nombre, tipoentidad, email, fonofijo, fonomovil) FROM stdin;
\.
COPY public.entidad (id_entidad, rut, nombre, tipoentidad, email, fonofijo, fonomovil) FROM '$$PATH$$/4974.dat';

--
-- Data for Name: entidadcomercial; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.entidadcomercial (id_entidad, rut, nombre, tipoentidad, fonofijo, fonomovil, email) FROM stdin;
\.
COPY public.entidadcomercial (id_entidad, rut, nombre, tipoentidad, fonofijo, fonomovil, email) FROM '$$PATH$$/4976.dat';

--
-- Data for Name: facturas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.facturas (numerofactura, fecha, tipo, cantidad, valor, subtotal, comision, gasto, adjuntofactura, id_tipoinversion, preciounitario, nombreactivo, tipo_entidad, id_entidad, id_entidad_comercial) FROM stdin;
\.
COPY public.facturas (numerofactura, fecha, tipo, cantidad, valor, subtotal, comision, gasto, adjuntofactura, id_tipoinversion, preciounitario, nombreactivo, tipo_entidad, id_entidad, id_entidad_comercial) FROM '$$PATH$$/4980.dat';

--
-- Data for Name: fondosmutuos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.fondosmutuos (id_fondo, nombre, montoinvertido, rentabilidad, montofinal, id_entidad, comprobante, tiporiesgo, fechainicio, fechatermino, id_banco) FROM stdin;
\.
COPY public.fondosmutuos (id_fondo, nombre, montoinvertido, rentabilidad, montofinal, id_entidad, comprobante, tiporiesgo, fechainicio, fechatermino, id_banco) FROM '$$PATH$$/4984.dat';

--
-- Data for Name: parametros; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parametros (id_parametro, nombre, valor, fechaactualizacion) FROM stdin;
\.
COPY public.parametros (id_parametro, nombre, valor, fechaactualizacion) FROM '$$PATH$$/4996.dat';

--
-- Data for Name: polizas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.polizas (numero, tipoasegurado, fechainicio, fechatermino, monto, adjuntopoliza) FROM stdin;
\.
COPY public.polizas (numero, tipoasegurado, fechainicio, fechatermino, monto, adjuntopoliza) FROM '$$PATH$$/4986.dat';

--
-- Data for Name: tipoinversion; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tipoinversion (id, nombre) FROM stdin;
\.
COPY public.tipoinversion (id, nombre) FROM '$$PATH$$/4978.dat';

--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, nombreusuario, "contraseña") FROM stdin;
\.
COPY public.usuarios (id, nombreusuario, "contraseña") FROM '$$PATH$$/4994.dat';

--
-- Name: accion_id_accion_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accion_id_accion_seq', 1, false);


--
-- Name: boletagarantia_numero_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.boletagarantia_numero_seq', 2, true);


--
-- Name: depositoaplazo_id_deposito_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.depositoaplazo_id_deposito_seq', 4, true);


--
-- Name: dividendos_id_dividendo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dividendos_id_dividendo_seq', 8, true);


--
-- Name: entidad_id_entidad_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.entidad_id_entidad_seq', 39, true);


--
-- Name: entidadcomercial_id_entidad_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.entidadcomercial_id_entidad_seq', 38, true);


--
-- Name: facturas_numerofactura_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.facturas_numerofactura_seq', 1, false);


--
-- Name: fondosmutuos_id_fondo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.fondosmutuos_id_fondo_seq', 18, true);


--
-- Name: parametros_id_parametro_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parametros_id_parametro_seq', 12, true);


--
-- Name: polizas_numero_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.polizas_numero_seq', 1, false);


--
-- Name: tipoinversion_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tipoinversion_id_seq', 2, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 1, true);


--
-- Name: accion accion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accion
    ADD CONSTRAINT accion_pkey PRIMARY KEY (id_accion);


--
-- Name: accion accion_ticker_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accion
    ADD CONSTRAINT accion_ticker_key UNIQUE (ticker);


--
-- Name: boletagarantia boletagarantia_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_pkey PRIMARY KEY (numero);


--
-- Name: depositoaplazo depositoaplazo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_pkey PRIMARY KEY (id_deposito);


--
-- Name: dividendos dividendos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT dividendos_pkey PRIMARY KEY (id_dividendo);


--
-- Name: entidad entidad_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidad
    ADD CONSTRAINT entidad_pkey PRIMARY KEY (id_entidad);


--
-- Name: entidad entidad_rut_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidad
    ADD CONSTRAINT entidad_rut_key UNIQUE (rut);


--
-- Name: entidadcomercial entidadcomercial_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidadcomercial
    ADD CONSTRAINT entidadcomercial_pkey PRIMARY KEY (id_entidad);


--
-- Name: entidadcomercial entidadcomercial_rut_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entidadcomercial
    ADD CONSTRAINT entidadcomercial_rut_key UNIQUE (rut);


--
-- Name: facturas facturas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_pkey PRIMARY KEY (numerofactura);


--
-- Name: fondosmutuos fondosmutuos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_pkey PRIMARY KEY (id_fondo);


--
-- Name: parametros parametros_nombre_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametros
    ADD CONSTRAINT parametros_nombre_key UNIQUE (nombre);


--
-- Name: parametros parametros_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parametros
    ADD CONSTRAINT parametros_pkey PRIMARY KEY (id_parametro);


--
-- Name: polizas polizas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.polizas
    ADD CONSTRAINT polizas_pkey PRIMARY KEY (numero);


--
-- Name: tipoinversion tipoinversion_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tipoinversion
    ADD CONSTRAINT tipoinversion_pkey PRIMARY KEY (id);


--
-- Name: usuarios usuarios_nombreusuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_nombreusuario_key UNIQUE (nombreusuario);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: facturas before_update_facturas; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER before_update_facturas BEFORE INSERT OR UPDATE ON public.facturas FOR EACH ROW EXECUTE FUNCTION public.update_subtotal();


--
-- Name: depositoaplazo trigger_actualizar_plazo; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_actualizar_plazo BEFORE INSERT OR UPDATE ON public.depositoaplazo FOR EACH ROW EXECUTE FUNCTION public.actualizar_plazo();

ALTER TABLE public.depositoaplazo DISABLE TRIGGER trigger_actualizar_plazo;


--
-- Name: dividendos trigger_calcular_rentabilidad; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_calcular_rentabilidad BEFORE INSERT OR UPDATE ON public.dividendos FOR EACH ROW EXECUTE FUNCTION public.calcular_rentabilidad();


--
-- Name: facturas trigger_calcular_valor; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_calcular_valor BEFORE INSERT OR UPDATE ON public.facturas FOR EACH ROW EXECUTE FUNCTION public.calcular_valor_factura();


--
-- Name: boletagarantia boletagarantia_id_banco_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);


--
-- Name: boletagarantia boletagarantia_id_cliente_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT boletagarantia_id_cliente_fkey FOREIGN KEY (id_beneficiario) REFERENCES public.entidadcomercial(id_entidad);


--
-- Name: depositoaplazo depositoaplazo_id_banco_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);


--
-- Name: depositoaplazo depositoaplazo_id_empresa_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT depositoaplazo_id_empresa_fkey FOREIGN KEY (id_entidadcomercial) REFERENCES public.entidadcomercial(id_entidad);


--
-- Name: dividendos dividendos_id_accion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT dividendos_id_accion_fkey FOREIGN KEY (id_accion) REFERENCES public.accion(id_accion);


--
-- Name: facturas facturas_entidad_comercial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_entidad_comercial_fkey FOREIGN KEY (id_entidad_comercial) REFERENCES public.entidadcomercial(id_entidad) ON DELETE CASCADE;


--
-- Name: facturas facturas_entidad_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_entidad_fkey FOREIGN KEY (id_entidad) REFERENCES public.entidad(id_entidad) ON DELETE CASCADE;


--
-- Name: facturas facturas_id_tipoinversion_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.facturas
    ADD CONSTRAINT facturas_id_tipoinversion_fkey FOREIGN KEY (id_tipoinversion) REFERENCES public.tipoinversion(id);


--
-- Name: dividendos fk_accion; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dividendos
    ADD CONSTRAINT fk_accion FOREIGN KEY (id_accion) REFERENCES public.accion(id_accion);


--
-- Name: boletagarantia fk_boleta_empresa; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.boletagarantia
    ADD CONSTRAINT fk_boleta_empresa FOREIGN KEY (id_empresa) REFERENCES public.entidadcomercial(id_entidad);


--
-- Name: depositoaplazo fk_deposito_id_entidadcomercial; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.depositoaplazo
    ADD CONSTRAINT fk_deposito_id_entidadcomercial FOREIGN KEY (id_entidadcomercial) REFERENCES public.entidadcomercial(id_entidad);


--
-- Name: fondosmutuos fondosmutuos_id_banco_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_id_banco_fkey FOREIGN KEY (id_banco) REFERENCES public.entidad(id_entidad);


--
-- Name: fondosmutuos fondosmutuos_id_entidadcomercial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fondosmutuos
    ADD CONSTRAINT fondosmutuos_id_entidadcomercial_fkey FOREIGN KEY (id_entidad) REFERENCES public.entidadcomercial(id_entidad);


--
-- PostgreSQL database dump complete
--

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       