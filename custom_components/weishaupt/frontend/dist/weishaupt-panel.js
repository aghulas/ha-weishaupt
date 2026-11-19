var H=globalThis,L=H.ShadowRoot&&(H.ShadyCSS===void 0||H.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,B=Symbol(),ne=new WeakMap,k=class{constructor(e,s,t){if(this._$cssResult$=!0,t!==B)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=s}get styleSheet(){let e=this.o,s=this.t;if(L&&e===void 0){let t=s!==void 0&&s.length===1;t&&(e=ne.get(s)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),t&&ne.set(s,e))}return e}toString(){return this.cssText}},re=n=>new k(typeof n=="string"?n:n+"",void 0,B),V=(n,...e)=>{let s=n.length===1?n[0]:e.reduce((t,i,r)=>t+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[r+1],n[0]);return new k(s,n,B)},oe=(n,e)=>{if(L)n.adoptedStyleSheets=e.map(s=>s instanceof CSSStyleSheet?s:s.styleSheet);else for(let s of e){let t=document.createElement("style"),i=H.litNonce;i!==void 0&&t.setAttribute("nonce",i),t.textContent=s.cssText,n.appendChild(t)}},W=L?n=>n:n=>n instanceof CSSStyleSheet?(e=>{let s="";for(let t of e.cssRules)s+=t.cssText;return re(s)})(n):n;var{is:Te,defineProperty:Me,getOwnPropertyDescriptor:Pe,getOwnPropertyNames:Oe,getOwnPropertySymbols:Ne,getPrototypeOf:Ue}=Object,D=globalThis,ae=D.trustedTypes,He=ae?ae.emptyScript:"",Le=D.reactiveElementPolyfillSupport,C=(n,e)=>n,q={toAttribute(n,e){switch(e){case Boolean:n=n?He:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,e){let s=n;switch(e){case Boolean:s=n!==null;break;case Number:s=n===null?null:Number(n);break;case Object:case Array:try{s=JSON.parse(n)}catch{s=null}}return s}},de=(n,e)=>!Te(n,e),le={attribute:!0,type:String,converter:q,reflect:!1,useDefault:!1,hasChanged:de};Symbol.metadata??=Symbol("metadata"),D.litPropertyMetadata??=new WeakMap;var $=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,s=le){if(s.state&&(s.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((s=Object.create(s)).wrapped=!0),this.elementProperties.set(e,s),!s.noAccessor){let t=Symbol(),i=this.getPropertyDescriptor(e,t,s);i!==void 0&&Me(this.prototype,e,i)}}static getPropertyDescriptor(e,s,t){let{get:i,set:r}=Pe(this.prototype,e)??{get(){return this[s]},set(o){this[s]=o}};return{get:i,set(o){let l=i?.call(this);r?.call(this,o),this.requestUpdate(e,l,t)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??le}static _$Ei(){if(this.hasOwnProperty(C("elementProperties")))return;let e=Ue(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(C("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(C("properties"))){let s=this.properties,t=[...Oe(s),...Ne(s)];for(let i of t)this.createProperty(i,s[i])}let e=this[Symbol.metadata];if(e!==null){let s=litPropertyMetadata.get(e);if(s!==void 0)for(let[t,i]of s)this.elementProperties.set(t,i)}this._$Eh=new Map;for(let[s,t]of this.elementProperties){let i=this._$Eu(s,t);i!==void 0&&this._$Eh.set(i,s)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let s=[];if(Array.isArray(e)){let t=new Set(e.flat(1/0).reverse());for(let i of t)s.unshift(W(i))}else e!==void 0&&s.push(W(e));return s}static _$Eu(e,s){let t=s.attribute;return t===!1?void 0:typeof t=="string"?t:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,s=this.constructor.elementProperties;for(let t of s.keys())this.hasOwnProperty(t)&&(e.set(t,this[t]),delete this[t]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return oe(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,s,t){this._$AK(e,t)}_$ET(e,s){let t=this.constructor.elementProperties.get(e),i=this.constructor._$Eu(e,t);if(i!==void 0&&t.reflect===!0){let r=(t.converter?.toAttribute!==void 0?t.converter:q).toAttribute(s,t.type);this._$Em=e,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(e,s){let t=this.constructor,i=t._$Eh.get(e);if(i!==void 0&&this._$Em!==i){let r=t.getPropertyOptions(i),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:q;this._$Em=i;let l=o.fromAttribute(s,r.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(e,s,t,i=!1,r){if(e!==void 0){let o=this.constructor;if(i===!1&&(r=this[e]),t??=o.getPropertyOptions(e),!((t.hasChanged??de)(r,s)||t.useDefault&&t.reflect&&r===this._$Ej?.get(e)&&!this.hasAttribute(o._$Eu(e,t))))return;this.C(e,s,t)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,s,{useDefault:t,reflect:i,wrapped:r},o){t&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,o??s??this[e]),r!==!0||o!==void 0)||(this._$AL.has(e)||(this.hasUpdated||t||(s=void 0),this._$AL.set(e,s)),i===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(s){Promise.reject(s)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let t=this.constructor.elementProperties;if(t.size>0)for(let[i,r]of t){let{wrapped:o}=r,l=this[i];o!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,r,l)}}let e=!1,s=this._$AL;try{e=this.shouldUpdate(s),e?(this.willUpdate(s),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(s)):this._$EM()}catch(t){throw e=!1,this._$EM(),t}e&&this._$AE(s)}willUpdate(e){}_$AE(e){this._$EO?.forEach(s=>s.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(s=>this._$ET(s,this[s])),this._$EM()}updated(e){}firstUpdated(e){}};$.elementStyles=[],$.shadowRootOptions={mode:"open"},$[C("elementProperties")]=new Map,$[C("finalized")]=new Map,Le?.({ReactiveElement:$}),(D.reactiveElementVersions??=[]).push("2.1.2");var Z=globalThis,ce=n=>n,I=Z.trustedTypes,he=I?I.createPolicy("lit-html",{createHTML:n=>n}):void 0,fe="$lit$",b=`lit$${Math.random().toFixed(9).slice(2)}$`,$e="?"+b,De=`<${$e}>`,x=document,T=()=>x.createComment(""),M=n=>n===null||typeof n!="object"&&typeof n!="function",Q=Array.isArray,Ie=n=>Q(n)||typeof n?.[Symbol.iterator]=="function",F=`[ 	
\f\r]`,R=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,ue=/-->/g,pe=/>/g,y=RegExp(`>|${F}(?:([^\\s"'>=/]+)(${F}*=${F}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),_e=/'/g,ge=/"/g,be=/^(?:script|style|textarea|title)$/i,ee=n=>(e,...s)=>({_$litType$:n,strings:e,values:s}),c=ee(1),Ye=ee(2),Xe=ee(3),A=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),me=new WeakMap,w=x.createTreeWalker(x,129);function ve(n,e){if(!Q(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return he!==void 0?he.createHTML(e):e}var je=(n,e)=>{let s=n.length-1,t=[],i,r=e===2?"<svg>":e===3?"<math>":"",o=R;for(let l=0;l<s;l++){let d=n[l],_,p,u=-1,m=0;for(;m<d.length&&(o.lastIndex=m,p=o.exec(d),p!==null);)m=o.lastIndex,o===R?p[1]==="!--"?o=ue:p[1]!==void 0?o=pe:p[2]!==void 0?(be.test(p[2])&&(i=RegExp("</"+p[2],"g")),o=y):p[3]!==void 0&&(o=y):o===y?p[0]===">"?(o=i??R,u=-1):p[1]===void 0?u=-2:(u=o.lastIndex-p[2].length,_=p[1],o=p[3]===void 0?y:p[3]==='"'?ge:_e):o===ge||o===_e?o=y:o===ue||o===pe?o=R:(o=y,i=void 0);let f=o===y&&n[l+1].startsWith("/>")?" ":"";r+=o===R?d+De:u>=0?(t.push(_),d.slice(0,u)+fe+d.slice(u)+b+f):d+b+(u===-2?l:f)}return[ve(n,r+(n[s]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),t]},P=class n{constructor({strings:e,_$litType$:s},t){let i;this.parts=[];let r=0,o=0,l=e.length-1,d=this.parts,[_,p]=je(e,s);if(this.el=n.createElement(_,t),w.currentNode=this.el.content,s===2||s===3){let u=this.el.content.firstChild;u.replaceWith(...u.childNodes)}for(;(i=w.nextNode())!==null&&d.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let u of i.getAttributeNames())if(u.endsWith(fe)){let m=p[o++],f=i.getAttribute(u).split(b),U=/([.?@])?(.*)/.exec(m);d.push({type:1,index:r,name:U[2],strings:f,ctor:U[1]==="."?J:U[1]==="?"?G:U[1]==="@"?Y:S}),i.removeAttribute(u)}else u.startsWith(b)&&(d.push({type:6,index:r}),i.removeAttribute(u));if(be.test(i.tagName)){let u=i.textContent.split(b),m=u.length-1;if(m>0){i.textContent=I?I.emptyScript:"";for(let f=0;f<m;f++)i.append(u[f],T()),w.nextNode(),d.push({type:2,index:++r});i.append(u[m],T())}}}else if(i.nodeType===8)if(i.data===$e)d.push({type:2,index:r});else{let u=-1;for(;(u=i.data.indexOf(b,u+1))!==-1;)d.push({type:7,index:r}),u+=b.length-1}r++}}static createElement(e,s){let t=x.createElement("template");return t.innerHTML=e,t}};function E(n,e,s=n,t){if(e===A)return e;let i=t!==void 0?s._$Co?.[t]:s._$Cl,r=M(e)?void 0:e._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(n),i._$AT(n,s,t)),t!==void 0?(s._$Co??=[])[t]=i:s._$Cl=i),i!==void 0&&(e=E(n,i._$AS(n,e.values),i,t)),e}var K=class{constructor(e,s){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=s}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:s},parts:t}=this._$AD,i=(e?.creationScope??x).importNode(s,!0);w.currentNode=i;let r=w.nextNode(),o=0,l=0,d=t[0];for(;d!==void 0;){if(o===d.index){let _;d.type===2?_=new O(r,r.nextSibling,this,e):d.type===1?_=new d.ctor(r,d.name,d.strings,this,e):d.type===6&&(_=new X(r,this,e)),this._$AV.push(_),d=t[++l]}o!==d?.index&&(r=w.nextNode(),o++)}return w.currentNode=x,i}p(e){let s=0;for(let t of this._$AV)t!==void 0&&(t.strings!==void 0?(t._$AI(e,t,s),s+=t.strings.length-2):t._$AI(e[s])),s++}},O=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,s,t,i){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=e,this._$AB=s,this._$AM=t,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,s=this._$AM;return s!==void 0&&e?.nodeType===11&&(e=s.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,s=this){e=E(this,e,s),M(e)?e===h||e==null||e===""?(this._$AH!==h&&this._$AR(),this._$AH=h):e!==this._$AH&&e!==A&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Ie(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==h&&M(this._$AH)?this._$AA.nextSibling.data=e:this.T(x.createTextNode(e)),this._$AH=e}$(e){let{values:s,_$litType$:t}=e,i=typeof t=="number"?this._$AC(e):(t.el===void 0&&(t.el=P.createElement(ve(t.h,t.h[0]),this.options)),t);if(this._$AH?._$AD===i)this._$AH.p(s);else{let r=new K(i,this),o=r.u(this.options);r.p(s),this.T(o),this._$AH=r}}_$AC(e){let s=me.get(e.strings);return s===void 0&&me.set(e.strings,s=new P(e)),s}k(e){Q(this._$AH)||(this._$AH=[],this._$AR());let s=this._$AH,t,i=0;for(let r of e)i===s.length?s.push(t=new n(this.O(T()),this.O(T()),this,this.options)):t=s[i],t._$AI(r),i++;i<s.length&&(this._$AR(t&&t._$AB.nextSibling,i),s.length=i)}_$AR(e=this._$AA.nextSibling,s){for(this._$AP?.(!1,!0,s);e!==this._$AB;){let t=ce(e).nextSibling;ce(e).remove(),e=t}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},S=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,s,t,i,r){this.type=1,this._$AH=h,this._$AN=void 0,this.element=e,this.name=s,this._$AM=i,this.options=r,t.length>2||t[0]!==""||t[1]!==""?(this._$AH=Array(t.length-1).fill(new String),this.strings=t):this._$AH=h}_$AI(e,s=this,t,i){let r=this.strings,o=!1;if(r===void 0)e=E(this,e,s,0),o=!M(e)||e!==this._$AH&&e!==A,o&&(this._$AH=e);else{let l=e,d,_;for(e=r[0],d=0;d<r.length-1;d++)_=E(this,l[t+d],s,d),_===A&&(_=this._$AH[d]),o||=!M(_)||_!==this._$AH[d],_===h?e=h:e!==h&&(e+=(_??"")+r[d+1]),this._$AH[d]=_}o&&!i&&this.j(e)}j(e){e===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},J=class extends S{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===h?void 0:e}},G=class extends S{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==h)}},Y=class extends S{constructor(e,s,t,i,r){super(e,s,t,i,r),this.type=5}_$AI(e,s=this){if((e=E(this,e,s,0)??h)===A)return;let t=this._$AH,i=e===h&&t!==h||e.capture!==t.capture||e.once!==t.once||e.passive!==t.passive,r=e!==h&&(t===h||i);i&&this.element.removeEventListener(this.name,this,t),r&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},X=class{constructor(e,s,t){this.element=e,this.type=6,this._$AN=void 0,this._$AM=s,this.options=t}get _$AU(){return this._$AM._$AU}_$AI(e){E(this,e)}};var ze=Z.litHtmlPolyfillSupport;ze?.(P,O),(Z.litHtmlVersions??=[]).push("3.3.3");var ye=(n,e,s)=>{let t=s?.renderBefore??e,i=t._$litPart$;if(i===void 0){let r=s?.renderBefore??null;t._$litPart$=i=new O(e.insertBefore(T(),r),r,void 0,s??{})}return i._$AI(n),i};var te=globalThis,v=class extends ${constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let s=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=ye(s,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return A}};v._$litElement$=!0,v.finalized=!0,te.litElementHydrateSupport?.({LitElement:v});var Be=te.litElementPolyfillSupport;Be?.({LitElement:v});(te.litElementVersions??=[]).push("4.2.2");var Ve="-",se={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read: enable the program sensor or its day entities",write_hint:"Changes are made in the entity (button Open); the panel only shows. Comfort: written at once; regulation: after a confirmation in Repairs.",description:"Description"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"non lu : activez le capteur du programme ou ses entit\xE9s de jour",write_hint:"Les modifications se font dans l'entit\xE9 (bouton Ouvrir) ; le panneau ne fait qu'afficher. Confort : \xE9crit aussit\xF4t ; r\xE9gulation : apr\xE8s une confirmation dans R\xE9parations.",description:"Description"}},ie={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function xe(n){let e=(n??"en").split("-")[0];return e in se?e:"en"}function a(n,e,s={}){return(se[n]?.[e]??se.en[e]??e).replace(/\{(\w+)\}/g,(i,r)=>String(s[r]??`{${r}}`))}function g(n,e){return n?n[e]??n.en??Object.values(n)[0]??"":""}function Ae(n,e,s){if(!e)return null;let t=e.values[n.index];if(t===void 0)return null;if(t===Ve)return a(s,"not_available");if(n.values){let i=n.values[t];return i?g(i,s):t}return n.unit?`${t} ${n.unit}`:t}function Ee(n,e){let s=t=>t.split(" (")[0].trim().toLowerCase();return!n||s(n)===s(e)}function Se(n){return n.read?!n.entity_id&&!n.passive?"not_listened":"waiting":"not_loaded"}function ke(n,e){let s=Math.max(0,Math.round(n));return s<90?a(e,"seconds_ago",{n:s}):s<90*60?a(e,"minutes_ago",{n:Math.round(s/60)}):s<36*3600?a(e,"hours_ago",{n:Math.round(s/3600)}):a(e,"days_ago",{n:Math.round(s/86400)})}function Ce(n){let e=n.range;if(!e)return"";let s=n.unit?` ${n.unit}`:"",t=`${e.min??"\u2026"} \u2013 ${e.max??"\u2026"}${s}`;return e.step?`${t} (${e.step})`:t}function we(n){let[e,s]=n.split(":").map(t=>Number(t));return e*60+(s||0)}function Re(n){return n.map(([e,s])=>{let t=we(e),i=we(s);return{left:t/1440*100,width:Math.max(0,i-t)/1440*100,text:`${e}-${s}`}})}function j(n){let e=[],s=(t,i)=>{for(let r of n.filter(o=>o.parent===t))e.push([r,i]),s(r.id,i+1)};s("",0);for(let t of n)e.some(([i])=>i.id===t.id)||e.push([t,0]);return e}var z="__definitions__";function We(n,e,s){let t=n.find(i=>i.id===e)?.parent??"";for(;t;){if(t===s)return!0;t=n.find(i=>i.id===t)?.parent??""}return!1}var qe="programs",N=class extends v{constructor(){super();this._offset=0;this._readings={},this._programs={},this._available=!0,this._tick=0}get _lang(){return xe(this.hass?.language)}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>this._tick+=1,3e4),this._entryId&&this._subscribe(this._entryId)}disconnectedCallback(){super.disconnectedCallback(),window.clearInterval(this._timer),this._unsubscribe?.(),this._unsubscribe=void 0}willUpdate(s){s.has("hass")&&this.hass&&this._installations===void 0&&!this._loading&&(this._loading="installations",this.hass.callWS({type:"weishaupt/panel/installations"}).then(t=>{this._installations=t,t.length&&this._select(t[0].entry_id)}).catch(t=>this._error=t.message))}async _select(s){this._entryId=s,this._tree=void 0,this._readings={},this._programs={};try{let t=await this.hass.callWS({type:"weishaupt/panel/tree",entry_id:s});this._tree=t,this._device=t.devices[0]?.id,this._menu=t.devices[0]?.menus[0]?.id,await this._subscribe(s)}catch(t){this._error=t.message}}async _subscribe(s){this._unsubscribe?.(),this._unsubscribe=await this.hass.connection.subscribeMessage(t=>this._live(t),{type:"weishaupt/panel/subscribe",entry_id:s})}_live(s){this._offset=Date.now()/1e3-s.now,s.available!==void 0&&(this._available=s.available),s.readings&&(this._readings={...this._readings,...s.readings}),s.programs&&(this._programs={...this._programs,...s.programs})}_open(s){this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:s},bubbles:!0,composed:!0}))}_age(s){return ke(Date.now()/1e3-this._offset-s.when,this._lang)}render(){let s=this._lang;return this._error?c`<div class="message error" role="alert">${this._error}</div>`:this._installations===void 0?c`<div class="message">${a(s,"loading")}</div>`:this._installations.length?c`
      <header>
        <h1>${a(s,"title")}</h1>
        ${this._installations.length>1?c`<label
              >${a(s,"installation")}
              <select @change=${t=>this._select(t.target.value)}>
                ${this._installations.map(t=>c`<option value=${t.entry_id} ?selected=${t.entry_id===this._entryId}>${t.title}</option>`)}
              </select></label
            >`:h}
        ${this._clock()}
      </header>
      ${this._available?h:c`<div class="message warning" role="status">${a(s,"unavailable")}</div>`}
      ${this._tree?this._body(this._tree):c`<div class="message">${a(s,"loading")}</div>`}
    `:c`<div class="message">${a(s,"no_installation")}</div>`}_clock(){let s=this._tree?.clock.entity_id,t=s?this.hass.states[s]:void 0;if(!s||!t||Number.isNaN(Number(t.state)))return h;let i=this._lang,r=Math.round(Number(t.state)),o=r===0?a(i,"clock_on_time"):a(i,r>0?"clock_ahead":"clock_behind",{n:Math.abs(r)});return c`<button class="clock link" @click=${()=>this._open(s)}>
      ${a(i,"clock_line",{label:a(i,"clock_offset"),text:o})}
    </button>`}_body(s){let t=s.devices.find(i=>i.id===this._device);return c`<div class=${this.narrow?"layout narrow":"layout"}>
      <nav aria-label=${a(this._lang,"devices")}>${this._nav(s)}</nav>
      <main>${this._menu===z?this._definitions(s):t?this._device_view(t):h}</main>
    </div>`}_nav(s){let t=this._lang;if(this.narrow){let r=`${this._device??""}|${this._menu??""}`;return c`<label class="choose"
        >${a(t,"devices")}
        <select
          @change=${o=>{let[l,d]=o.target.value.split("|");this._device=l,this._menu=d}}
        >
          ${s.devices.map(o=>c`<optgroup label=${g(o.label,t)}>
              ${j(o.menus).map(([l,d])=>c`<option value=${`${o.id}|${l.id}`} ?selected=${r===`${o.id}|${l.id}`}>
                    ${"\xA0\xA0".repeat(d)}${g(l.label,t)}
                  </option>`)}
            </optgroup>`)}
          <option value=${`${this._device??""}|${z}`} ?selected=${this._menu===z}>
            ${a(t,"definitions")}
          </option>
        </select></label
      >`}let i=(r,o,l,d)=>{let _=this._device===r&&this._menu===o;return c`<li>
        <button
          class="menu depth${d}"
          aria-current=${_?"page":"false"}
          @click=${()=>{this._device=r,this._menu=o}}
        >
          ${l}
        </button>
      </li>`};return c`<ul>
      ${s.devices.map(r=>c`<li>
          <span class="device">${g(r.label,t)}</span>
          <ul>
            ${j(r.menus).map(([o,l])=>i(r.id,o.id,g(o.label,t),l))}
          </ul>
        </li>`)}
      ${i(this._device??"",z,a(t,"definitions"),0)}
    </ul>`}_device_view(s){let t=this._lang,i=s.menus.find(l=>l.id===this._menu),r=[s.addresses.length?`${a(t,"address")} ${s.addresses.join(", ")}`:"",s.software?`${a(t,"software")} ${s.software}`:"",s.hardware?`${a(t,"hardware")} ${s.hardware}`:""].filter(Boolean),o=j(s.menus).filter(([l])=>l.id===this._menu||We(s.menus,l.id,this._menu??"")).map(([l])=>[l,s.rows.filter(d=>d.menu===l.id)]).filter(([,l])=>l.length);return c`<h2>${g(s.label,t)}${i?c` — ${g(i.label,t)}`:h}</h2>
      ${r.length?c`<p class="secondary">${r.join(" \xB7 ")}</p>`:h}
      ${this._menu===qe?this._programs_view(s):h}
      ${o.length?c`<p class="secondary">${a(t,"write_hint")}</p>`:h}
      ${o.map(([l,d])=>c`${l.id!==this._menu?c`<h3>${g(l.label,t)}</h3>`:h}${this._table(d)}`)}`}_table(s){let t=this._lang;return this._tick,c`<div class="scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">${a(t,"name")}</th>
              <th scope="col">${a(t,"value")}</th>
              <th scope="col">${a(t,"age")}</th>
              <th scope="col">${a(t,"range")}</th>
              <th scope="col">${a(t,"write")}</th>
              <th scope="col">${a(t,"entity")}</th>
            </tr>
          </thead>
          <tbody>
            ${s.map(i=>{let r=this._readings[i.message],o=Ae(i,r,t),l=Ee(g(i.description,t),g(i.label,t))?"":g(i.description,t);return c`<tr>
                <th scope="row">
                  ${g(i.label,t)}
                  ${l?c`<div class="description">${l}</div>`:h}
                </th>
                <td class="nowrap">${o??c`<span class="secondary">${a(t,Se(i))}</span>`}</td>
                <td class="secondary nowrap">
                  ${r?this._age(r):""}${i.passive?c`<div>${a(t,"passive")}</div>`:h}
                </td>
                <td class="nowrap">${Ce(i)}</td>
                <td>
                  ${i.writable?c`<span class="badge ${i.writable.risk}">${a(t,i.writable.risk)}</span>`:c`<span class="secondary">${a(t,"read_only")}</span>`}
                </td>
                <td>
                  ${i.entity_id?c`<button class="link" @click=${()=>this._open(i.entity_id)}>${a(t,"open")}</button>`:h}
                </td>
              </tr>`})}
          </tbody>
        </table>
      </div>`}_programs_view(s){let t=this._lang,i=ie[t]??ie.en;return c`${s.programs.map(r=>{let o=this._programs[r.key],l=r.read?r.listened?r.writable?a(t,"editable"):a(t,"not_editable"):a(t,"program_not_listened"):a(t,"not_read_program");return c`<section class="program">
        <h3>
          ${g(r.label,t)}
          ${r.entity_id?c`<button class="link" @click=${()=>this._open(r.entity_id)}>${a(t,"open")}</button>`:h}
        </h3>
        <p class="secondary">${l}</p>
        <table class="week">
          <caption class="visually-hidden">${g(r.label,t)}</caption>
          <thead>
            <tr>
              <th scope="col"><span class="visually-hidden">${a(t,"programs")}</span></th>
              <td class="scale" aria-hidden="true">
                ${[0,6,12,18,24].map(d=>c`<span style="left:${d/24*100}%">${d}</span>`)}
              </td>
            </tr>
          </thead>
          <tbody>
            ${i.map((d,_)=>{let p=o?.[String(_+1)],u=p==null?a(t,r.listened?"day_unread":"not_listened"):p.length?p.map(([m,f])=>`${m}-${f}`).join(", "):a(t,"day_none");return c`<tr>
                <th scope="row">${d}</th>
                <td>
                  <div class="day" aria-hidden="true">
                    ${(p??[]).length?Re(p).map(m=>c`<span class="bar" style="left:${m.left}%;width:${m.width}%"></span>`):h}
                  </div>
                  <div class="day-text">${u}</div>
                </td>
              </tr>`})}
          </tbody>
        </table>
      </section>`})}`}_definitions(s){let t=this._lang,i=s.definitions,r=l=>l.length?c`<ul>${l.map(d=>c`<li><code>${d}</code></li>`)}</ul>`:c`${a(t,"none")}`,o=s.writes;return c`<h2>${a(t,"definitions")}</h2>
      <dl>
        <dt>${a(t,"in_use")}</dt>
        <dd>
          ${i.version}${i.commit?c` <code>${i.commit.slice(0,7)}</code>`:h} —
          ${i.source==="bundled"?a(t,"source_bundled"):a(t,"source_file",{file:i.source})}
        </dd>
        <dt>${a(t,"messages")}</dt>
        <dd>${a(t,"usable",{usable:i.usable,messages:i.messages})}</dd>
        <dt>${a(t,"refused")}</dt>
        <dd>${r(Object.entries(i.refused).map(([l,d])=>`${l}: ${d}`))}</dd>
        <dt>${a(t,"mismatches")}</dt>
        <dd>${r(i.mismatches.map(l=>`${l.key}: ${l.reason}${l.detail?` (${l.detail})`:""}`))}</dd>
        <dt>${a(t,"named_from_metadata")}</dt>
        <dd>${r(i.named_from_metadata)}</dd>
        <dt>${a(t,"not_named")}</dt>
        <dd>${r(i.not_named)}</dd>
        <dt>${a(t,"ebusd")}</dt>
        <dd>${s.ebusd.version??"?"}${s.ebusd.own_address?` (${s.ebusd.own_address})`:""}</dd>
        <dt>${a(t,"unknown_addresses")}</dt>
        <dd>${r(s.unknown_addresses)}</dd>
        <dt>${a(t,"writes")}</dt>
        <dd>
          ${o?c`${a(t,o.switch?"switch_on":"switch_off")} ·
              ${a(t,"capability",{value:o.capability})} ·
              ${a(t,"per_hour",{n:o.writes_last_hour,max:o.max_per_hour})}`:a(t,"writes_off")}
        </dd>
      </dl>`}};N.properties={hass:{attribute:!1},narrow:{type:Boolean},_installations:{state:!0},_entryId:{state:!0},_tree:{state:!0},_readings:{state:!0},_programs:{state:!0},_available:{state:!0},_device:{state:!0},_menu:{state:!0},_error:{state:!0},_tick:{state:!0}},N.styles=V`
    :host {
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
      font-family: var(--paper-font-body1_-_font-family, inherit);
    }
    header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
      padding: 12px 16px;
      background: var(--app-header-background-color, var(--card-background-color));
      color: var(--app-header-text-color, var(--primary-text-color));
      border-bottom: 1px solid var(--divider-color);
    }
    h1 {
      font-size: 20px;
      font-weight: 400;
      margin: 0;
    }
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin: 0 0 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 500;
      margin: 16px 0 4px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(200px, 260px) 1fr;
      gap: 16px;
      padding: 16px;
    }
    .layout.narrow {
      grid-template-columns: 1fr;
    }
    nav,
    main {
      background: var(--card-background-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: 1px solid var(--divider-color);
      padding: 12px;
      min-width: 0;
    }
    nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    label.choose {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    select {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    .device {
      display: block;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    button {
      font: inherit;
      color: inherit;
    }
    button.menu {
      display: block;
      width: 100%;
      text-align: start;
      border: 0;
      background: none;
      padding: 6px 8px;
      border-radius: 6px;
      cursor: pointer;
    }
    button.menu.depth1 {
      padding-inline-start: 24px;
    }
    button.menu.depth2 {
      padding-inline-start: 40px;
    }
    button.menu[aria-current="page"] {
      background: var(--secondary-background-color);
      color: var(--primary-color);
      font-weight: 500;
    }
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 8px;
      cursor: pointer;
      color: var(--primary-color);
    }
    .nowrap {
      white-space: nowrap;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      text-align: start;
      vertical-align: top;
      padding: 6px 8px;
      border-bottom: 1px solid var(--divider-color);
    }
    thead th {
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    tbody th {
      font-weight: 400;
      min-width: 12em;
    }
    .description,
    .secondary {
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .badge {
      white-space: nowrap;
      border-radius: 10px;
      padding: 1px 8px;
      border: 1px solid currentColor;
    }
    .badge.comfort {
      color: var(--success-color, var(--primary-color));
    }
    .badge.regulation {
      color: var(--warning-color, var(--primary-color));
    }
    .message {
      padding: 16px;
    }
    .message.error {
      color: var(--error-color);
    }
    .message.warning {
      color: var(--warning-color);
    }
    table.week th {
      width: 8em;
    }
    .scale {
      position: relative;
      height: 1.4em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .day {
      position: relative;
      height: 14px;
      background: var(--secondary-background-color);
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    dl {
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 6px 16px;
    }
    dt {
      color: var(--secondary-text-color);
    }
    dd {
      margin: 0;
    }
    dd ul {
      margin: 0;
      padding-inline-start: 16px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    @media (max-width: 600px) {
      dl {
        grid-template-columns: 1fr;
      }
    }
  `;customElements.get("weishaupt-panel")||customElements.define("weishaupt-panel",N);export{N as WeishauptPanel};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
