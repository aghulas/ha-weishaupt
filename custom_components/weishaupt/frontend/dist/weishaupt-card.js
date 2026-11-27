var X=globalThis,J=X.ShadowRoot&&(X.ShadyCSS===void 0||X.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,te=Symbol(),ge=new WeakMap,D=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==te)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o,t=this.t;if(J&&e===void 0){let r=t!==void 0&&t.length===1;r&&(e=ge.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),r&&ge.set(t,e))}return e}toString(){return this.cssText}},be=o=>new D(typeof o=="string"?o:o+"",void 0,te),H=(o,...e)=>{let t=o.length===1?o[0]:e.reduce((r,n,s)=>r+(i=>{if(i._$cssResult$===!0)return i.cssText;if(typeof i=="number")return i;throw Error("Value passed to 'css' function must be a 'css' function result: "+i+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(n)+o[s+1],o[0]);return new D(t,o,te)},ye=(o,e)=>{if(J)o.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of e){let r=document.createElement("style"),n=X.litNonce;n!==void 0&&r.setAttribute("nonce",n),r.textContent=t.cssText,o.appendChild(r)}},re=J?o=>o:o=>o instanceof CSSStyleSheet?(e=>{let t="";for(let r of e.cssRules)t+=r.cssText;return be(t)})(o):o;var{is:Ke,defineProperty:Xe,getOwnPropertyDescriptor:Je,getOwnPropertyNames:Ye,getOwnPropertySymbols:Qe,getPrototypeOf:Ze}=Object,Y=globalThis,ve=Y.trustedTypes,Ge=ve?ve.emptyScript:"",et=Y.reactiveElementPolyfillSupport,O=(o,e)=>o,ne={toAttribute(o,e){switch(e){case Boolean:o=o?Ge:null;break;case Object:case Array:o=o==null?o:JSON.stringify(o)}return o},fromAttribute(o,e){let t=o;switch(e){case Boolean:t=o!==null;break;case Number:t=o===null?null:Number(o);break;case Object:case Array:try{t=JSON.parse(o)}catch{t=null}}return t}},$e=(o,e)=>!Ke(o,e),we={attribute:!0,type:String,converter:ne,reflect:!1,useDefault:!1,hasChanged:$e};Symbol.metadata??=Symbol("metadata"),Y.litPropertyMetadata??=new WeakMap;var v=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=we){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){let r=Symbol(),n=this.getPropertyDescriptor(e,r,t);n!==void 0&&Xe(this.prototype,e,n)}}static getPropertyDescriptor(e,t,r){let{get:n,set:s}=Je(this.prototype,e)??{get(){return this[t]},set(i){this[t]=i}};return{get:n,set(i){let d=n?.call(this);s?.call(this,i),this.requestUpdate(e,d,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??we}static _$Ei(){if(this.hasOwnProperty(O("elementProperties")))return;let e=Ze(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(O("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(O("properties"))){let t=this.properties,r=[...Ye(t),...Qe(t)];for(let n of r)this.createProperty(n,t[n])}let e=this[Symbol.metadata];if(e!==null){let t=litPropertyMetadata.get(e);if(t!==void 0)for(let[r,n]of t)this.elementProperties.set(r,n)}this._$Eh=new Map;for(let[t,r]of this.elementProperties){let n=this._$Eu(t,r);n!==void 0&&this._$Eh.set(n,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){let t=[];if(Array.isArray(e)){let r=new Set(e.flat(1/0).reverse());for(let n of r)t.unshift(re(n))}else e!==void 0&&t.push(re(e));return t}static _$Eu(e,t){let r=t.attribute;return r===!1?void 0:typeof r=="string"?r:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){let e=new Map,t=this.constructor.elementProperties;for(let r of t.keys())this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r]);e.size>0&&(this._$Ep=e)}createRenderRoot(){let e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ye(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,r){this._$AK(e,r)}_$ET(e,t){let r=this.constructor.elementProperties.get(e),n=this.constructor._$Eu(e,r);if(n!==void 0&&r.reflect===!0){let s=(r.converter?.toAttribute!==void 0?r.converter:ne).toAttribute(t,r.type);this._$Em=e,s==null?this.removeAttribute(n):this.setAttribute(n,s),this._$Em=null}}_$AK(e,t){let r=this.constructor,n=r._$Eh.get(e);if(n!==void 0&&this._$Em!==n){let s=r.getPropertyOptions(n),i=typeof s.converter=="function"?{fromAttribute:s.converter}:s.converter?.fromAttribute!==void 0?s.converter:ne;this._$Em=n;let d=i.fromAttribute(t,s.type);this[n]=d??this._$Ej?.get(n)??d,this._$Em=null}}requestUpdate(e,t,r,n=!1,s){if(e!==void 0){let i=this.constructor;if(n===!1&&(s=this[e]),r??=i.getPropertyOptions(e),!((r.hasChanged??$e)(s,t)||r.useDefault&&r.reflect&&s===this._$Ej?.get(e)&&!this.hasAttribute(i._$Eu(e,r))))return;this.C(e,t,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:r,reflect:n,wrapped:s},i){r&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,i??t??this[e]),s!==!0||i!==void 0)||(this._$AL.has(e)||(this.hasUpdated||r||(t=void 0),this._$AL.set(e,t)),n===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[n,s]of this._$Ep)this[n]=s;this._$Ep=void 0}let r=this.constructor.elementProperties;if(r.size>0)for(let[n,s]of r){let{wrapped:i}=s,d=this[n];i!==!0||this._$AL.has(n)||d===void 0||this.C(n,void 0,s,d)}}let e=!1,t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(r=>r.hostUpdate?.()),this.update(t)):this._$EM()}catch(r){throw e=!1,this._$EM(),r}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};v.elementStyles=[],v.shadowRootOptions={mode:"open"},v[O("elementProperties")]=new Map,v[O("finalized")]=new Map,et?.({ReactiveElement:v}),(Y.reactiveElementVersions??=[]).push("2.1.2");var ce=globalThis,xe=o=>o,Q=ce.trustedTypes,Ae=Q?Q.createPolicy("lit-html",{createHTML:o=>o}):void 0,Me="$lit$",x=`lit$${Math.random().toFixed(9).slice(2)}$`,Te="?"+x,tt=`<${Te}>`,S=document,N=()=>S.createComment(""),U=o=>o===null||typeof o!="object"&&typeof o!="function",ue=Array.isArray,rt=o=>ue(o)||typeof o?.[Symbol.iterator]=="function",se=`[ 	
\f\r]`,L=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Ee=/-->/g,ke=/>/g,E=RegExp(`>|${se}(?:([^\\s"'>=/]+)(${se}*=${se}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Se=/'/g,Re=/"/g,He=/^(?:script|style|textarea|title)$/i,pe=o=>(e,...t)=>({_$litType$:o,strings:e,values:t}),h=pe(1),ct=pe(2),ut=pe(3),R=Symbol.for("lit-noChange"),f=Symbol.for("lit-nothing"),Ce=new WeakMap,k=S.createTreeWalker(S,129);function Pe(o,e){if(!ue(o)||!o.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ae!==void 0?Ae.createHTML(e):e}var nt=(o,e)=>{let t=o.length-1,r=[],n,s=e===2?"<svg>":e===3?"<math>":"",i=L;for(let d=0;d<t;d++){let a=o[d],c,_,p=-1,u=0;for(;u<a.length&&(i.lastIndex=u,_=i.exec(a),_!==null);)u=i.lastIndex,i===L?_[1]==="!--"?i=Ee:_[1]!==void 0?i=ke:_[2]!==void 0?(He.test(_[2])&&(n=RegExp("</"+_[2],"g")),i=E):_[3]!==void 0&&(i=E):i===E?_[0]===">"?(i=n??L,p=-1):_[1]===void 0?p=-2:(p=i.lastIndex-_[2].length,c=_[1],i=_[3]===void 0?E:_[3]==='"'?Re:Se):i===Re||i===Se?i=E:i===Ee||i===ke?i=L:(i=E,n=void 0);let g=i===E&&o[d+1].startsWith("/>")?" ":"";s+=i===L?a+tt:p>=0?(r.push(c),a.slice(0,p)+Me+a.slice(p)+x+g):a+x+(p===-2?d:g)}return[Pe(o,s+(o[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),r]},z=class o{constructor({strings:e,_$litType$:t},r){let n;this.parts=[];let s=0,i=0,d=e.length-1,a=this.parts,[c,_]=nt(e,t);if(this.el=o.createElement(c,r),k.currentNode=this.el.content,t===2||t===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(n=k.nextNode())!==null&&a.length<d;){if(n.nodeType===1){if(n.hasAttributes())for(let p of n.getAttributeNames())if(p.endsWith(Me)){let u=_[i++],g=n.getAttribute(p).split(x),T=/([.?@])?(.*)/.exec(u);a.push({type:1,index:s,name:T[2],strings:g,ctor:T[1]==="."?ie:T[1]==="?"?ae:T[1]==="@"?de:j}),n.removeAttribute(p)}else p.startsWith(x)&&(a.push({type:6,index:s}),n.removeAttribute(p));if(He.test(n.tagName)){let p=n.textContent.split(x),u=p.length-1;if(u>0){n.textContent=Q?Q.emptyScript:"";for(let g=0;g<u;g++)n.append(p[g],N()),k.nextNode(),a.push({type:2,index:++s});n.append(p[u],N())}}}else if(n.nodeType===8)if(n.data===Te)a.push({type:2,index:s});else{let p=-1;for(;(p=n.data.indexOf(x,p+1))!==-1;)a.push({type:7,index:s}),p+=x.length-1}s++}}static createElement(e,t){let r=S.createElement("template");return r.innerHTML=e,r}};function P(o,e,t=o,r){if(e===R)return e;let n=r!==void 0?t._$Co?.[r]:t._$Cl,s=U(e)?void 0:e._$litDirective$;return n?.constructor!==s&&(n?._$AO?.(!1),s===void 0?n=void 0:(n=new s(o),n._$AT(o,t,r)),r!==void 0?(t._$Co??=[])[r]=n:t._$Cl=n),n!==void 0&&(e=P(o,n._$AS(o,e.values),n,r)),e}var oe=class{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){let{el:{content:t},parts:r}=this._$AD,n=(e?.creationScope??S).importNode(t,!0);k.currentNode=n;let s=k.nextNode(),i=0,d=0,a=r[0];for(;a!==void 0;){if(i===a.index){let c;a.type===2?c=new W(s,s.nextSibling,this,e):a.type===1?c=new a.ctor(s,a.name,a.strings,this,e):a.type===6&&(c=new le(s,this,e)),this._$AV.push(c),a=r[++d]}i!==a?.index&&(s=k.nextNode(),i++)}return k.currentNode=S,n}p(e){let t=0;for(let r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(e,r,t),t+=r.strings.length-2):r._$AI(e[t])),t++}},W=class o{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,r,n){this.type=2,this._$AH=f,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=r,this.options=n,this._$Cv=n?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode,t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=P(this,e,t),U(e)?e===f||e==null||e===""?(this._$AH!==f&&this._$AR(),this._$AH=f):e!==this._$AH&&e!==R&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):rt(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==f&&U(this._$AH)?this._$AA.nextSibling.data=e:this.T(S.createTextNode(e)),this._$AH=e}$(e){let{values:t,_$litType$:r}=e,n=typeof r=="number"?this._$AC(e):(r.el===void 0&&(r.el=z.createElement(Pe(r.h,r.h[0]),this.options)),r);if(this._$AH?._$AD===n)this._$AH.p(t);else{let s=new oe(n,this),i=s.u(this.options);s.p(t),this.T(i),this._$AH=s}}_$AC(e){let t=Ce.get(e.strings);return t===void 0&&Ce.set(e.strings,t=new z(e)),t}k(e){ue(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,r,n=0;for(let s of e)n===t.length?t.push(r=new o(this.O(N()),this.O(N()),this,this.options)):r=t[n],r._$AI(s),n++;n<t.length&&(this._$AR(r&&r._$AB.nextSibling,n),t.length=n)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){let r=xe(e).nextSibling;xe(e).remove(),e=r}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}},j=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,r,n,s){this.type=1,this._$AH=f,this._$AN=void 0,this.element=e,this.name=t,this._$AM=n,this.options=s,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=f}_$AI(e,t=this,r,n){let s=this.strings,i=!1;if(s===void 0)e=P(this,e,t,0),i=!U(e)||e!==this._$AH&&e!==R,i&&(this._$AH=e);else{let d=e,a,c;for(e=s[0],a=0;a<s.length-1;a++)c=P(this,d[r+a],t,a),c===R&&(c=this._$AH[a]),i||=!U(c)||c!==this._$AH[a],c===f?e=f:e!==f&&(e+=(c??"")+s[a+1]),this._$AH[a]=c}i&&!n&&this.j(e)}j(e){e===f?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}},ie=class extends j{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===f?void 0:e}},ae=class extends j{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==f)}},de=class extends j{constructor(e,t,r,n,s){super(e,t,r,n,s),this.type=5}_$AI(e,t=this){if((e=P(this,e,t,0)??f)===R)return;let r=this._$AH,n=e===f&&r!==f||e.capture!==r.capture||e.once!==r.once||e.passive!==r.passive,s=e!==f&&(r===f||n);n&&this.element.removeEventListener(this.name,this,r),s&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}},le=class{constructor(e,t,r){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(e){P(this,e)}};var st=ce.litHtmlPolyfillSupport;st?.(z,W),(ce.litHtmlVersions??=[]).push("3.3.3");var je=(o,e,t)=>{let r=t?.renderBefore??e,n=r._$litPart$;if(n===void 0){let s=t?.renderBefore??null;r._$litPart$=n=new W(e.insertBefore(N(),s),s,void 0,t??{})}return n._$AI(o),n};var he=globalThis,b=class extends v{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=je(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return R}};b._$litElement$=!0,b.finalized=!0,he.litElementHydrateSupport?.({LitElement:b});var ot=he.litElementPolyfillSupport;ot?.({LitElement:b});(he.litElementVersions??=[]).push("4.2.2");var _e={en:{title:"Weishaupt",installation:"Installation",devices:"Devices",definitions:"Definitions",programs:"Weekly programs",loading:"Loading\u2026",no_installation:"No Weishaupt installation is loaded.",unavailable:"ebusd does not answer: the values shown are the last ones read.",value:"Value",name:"Name",age:"Read",range:"Range",write:"Write",entity:"Entity",open:"Open",comfort:"comfort",regulation:"regulation",read_only:"read only",not_loaded:"not loaded by ebusd",not_listened:"not read: no enabled entity",waiting:"waiting for the first reading",not_available:"not available",seconds_ago:"{n} s ago",minutes_ago:"{n} min ago",hours_ago:"{n} h ago",days_ago:"{n} d ago",passive:"sent by the device",clock_offset:"Clock master",clock_line:"{label}: {text}",clock_ahead:"{n} s ahead",clock_behind:"{n} s behind",clock_on_time:"on time",software:"Software",hardware:"Hardware",address:"Bus address",in_use:"In use",source_bundled:"shipped with the integration",source_file:"file beside the configuration: {file}",refused:"Files not used",mismatches:"Differences with ebusd",named_from_metadata:"Entities named from the definitions",not_named:"Entities waiting for a name",messages:"Messages",usable:"{usable} of {messages} loaded by ebusd as described",writes:"Writes",writes_off:"disabled in the options",switch_on:"switch on",switch_off:"switch off",capability:"run-time checksum: {value}",mode_follow:"follows the running ebusd ({n} known)",mode_pinned:"pinned ({n} known)",per_hour:"{n} of {max} this hour",ebusd:"ebusd",unknown_addresses:"Addresses answering that no definition knows",none:"none",day_unread:"not read yet",day_none:"no range",editable:"editable through its program-day entities",not_editable:"read only: not proven writable on this device",not_read_program:"not loaded by ebusd",program_not_listened:"not read by any enabled entity: read it once now, or enable the program sensor to keep it up to date",write_hint:"Change a setting with its button Change (the writes switch must be on). Comfort: written at once and read back; regulation: after a confirmation in this panel. Open shows the entity.",description:"Description",no_sensor:"no sensor",kept:"kept from before the reload, read again soon",through:"through {circuit}",read_now:"Read now",read_cost:"{n} requests to the bus, about {s} s, once",read_queued:"{n} requests queued; the grid fills in as they are answered",readable:"{usable} of {readable} readable messages loaded by ebusd as described",not_usable:"Messages not read",reason_write_only:"write only",reason_device_absent:"device not on the bus",absent_circuit:"{circuit}: {n} messages, device not on the bus",reason_mismatch:"not loaded as described",reason_other:"not read",disabled:"disabled",reloading:"The integration was reloaded: loading again\u2026",read_only_settings:"Settings left read-only",edit:"Change",write_now:"Write",cancel:"Cancel",confirm:"Write to the controller",confirm_clock:"Send the time",confirm_title:"Confirm: {setting} \u2014 {device}",current:"Current value",new_value:"New value",allowed:"Allowed",path:"Written to bus address {address}, register {register}, from source address {source} ({source_text}). Read back right after.",path_short:"bus address {address}, register {register}, from {source}",regulation_note:"This setting changes how the heating is regulated: it is written after your confirmation.",comfort_note:"Comfort setting: written at once and read back.",writing:"Writing\u2026",written_line:"{before} \u2192 {after}{frame}: {result}",not_written:"Not written: {message}",not_offered_writes_disabled:"writes are not enabled in the options",not_offered:"not offered on this installation: {reason}",switch_off_hint:"The writes switch is off: turn it on to write.",edit_days:"Edit",write_days:"Write the changed days",discard:"Discard changes",copy_to:"Copy to",copy:"Copy",cost:"{days} days changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",cost_one:"1 day changed: up to {writes} writes (only changed slots are written); {used} of {max} this hour",interrupted:"no answer from Home Assistant (connection interrupted): the write may or may not have been sent; check the value read back",drag_hint:"Type the ranges, or drag on the bar to add one in quarters of an hour; a click on a range removes it.",day_format:"use HH:MM-HH:MM, up to three ranges, or -",day_quarter:"times must be quarters of an hour, from 00:00 to 24:00",day_order:"a range must end after it starts",day_too_many:"at most three ranges",day_overlap:"ranges must not overlap",set_clock:"Set the clock",clock_confirm:"Will send Home Assistant's time at second 00 of the next minute ({send_at}), to bus address fe from source address 31. If the bus is not free within {late} s of second 00, nothing is sent.",clock_sent:"Sent {requested} ({frame}): {result}",clock_current:"Clock master now: {current}",col_device:"Device",col_menu:"Menu",col_label:"Setting",col_value:"Value",col_unit:"Unit",col_range:"Range (step) or choices",col_writable:"Writable",col_code:"Vendor code",col_scheme:"Code scheme",code:"Code",code_title:"{scheme}, document {document}",sort_by_code:"Sort by vendor code",report_codes:"Vendor codes: {schemes}.",report:"Printable report",export_csv:"Export CSV",report_title:"Settings of the installation",report_subtitle:"{date} \xB7 definitions {version} \xB7 read by the Weishaupt integration of Home Assistant",report_no_factory:"Factory values: the definitions do not carry them yet. An empty value was not read when the report was made.",report_blocked:"The browser blocked the report window: allow pop-ups for Home Assistant and try again.",faults:"Faults",fault_history:"Fault history",fault_counters:"Fault counters",fault_log:"Fault log of the system manager (selected entry)",fault_code:"Code",fault_text:"Text",fault_slot:"Slot",fault_values:"Values stored with it",fault_number:"Fault",fault_count:"Count",fault_none:"no fault stored",fault_unordered:"Order unknown: the pointer to the last entry is not read.",fault_no_time:"The boiler stores no time with an entry.",fault_log_fields:"Entry {id}: code {code}, type {type}, origin {device}, {time}",fault_log_hint:"The operating unit of the system manager selects the entry shown; selecting another one is a write, which the panel does not do.",faults_unread:"{n} of these messages are read by no enabled entity.",faults_read_once:"Read once on demand: not kept up to date unless their entities are enabled.",read_nothing:"Nothing to request: these messages are already read by enabled entities or waiting.",card_name:"Weishaupt weekly program",card_description:"The week grid of one weekly program of a Weishaupt controller.",card_no_entity:"Choose a program sensor of the Weishaupt integration in the card's settings.",card_missing:"{entity} does not exist, or is disabled: enable it in Settings \u2192 Entities (program sensors are created disabled).",card_unavailable:"{entity} is unavailable: ebusd or the controller does not answer.",card_unread:"not read yet",card_editor_entity:"Program sensor",card_editor_title:"Title (optional)",card_editor_today:"Mark today",card_editor_hint:"Program sensors are created disabled: a program not listed here is enabled in Settings \u2192 Entities.",card_edit:"Edit",card_edited_on:"Read from the store of {device}: change this program there.",edited_on_program:"Read from the store of {device}: change {program} of {device}; a change sent here would be acknowledged and lost.",edited_on_setting:"kept by {device}: changed there",stored_only_badge:"stored only",stored_only_note:"Stored in this device only: not followed by the installation (hot water follows the system manager).",card_type_hint:"Type up to three ranges a day, HH:MM-HH:MM, or - for none; only changed days are written.",card_edit_admin:"Days are changed by administrators, here or in the Weishaupt panel.",card_not_writable:"This program is not proven writable on its device: read only.",card_writing_day:"{day}: writing\u2026",card_written_day:"{day}: written and read back",card_failed_day:"{day}: not written: {message}",card_no_switch:"Writes are not enabled in the options of the integration.",read_queued_one:"1 request queued (about {s} s).",read_queued_n:"{n} requests queued (about {s} s).",read_after_first_pass:"They come after the first pass that follows a start: {n} reads still due, {wait}.",read_after_queue:"They come after {n} reads already due, {wait}.",about_s:"about {n} s",about_min:"about {n} min",read_scope_menu:"Read this menu once",read_scope_device:"Read this device once",read_scope_all:"Read everything once",read_scope_hint:"Rows no enabled entity follows are read once, at the pace of the bus, after what the entities wait for.",read_price_one:"1 request, {time}.",read_price_n:"{n} requests, {time}.",read_start:"Start",read_stop:"Stop",dismiss:"Close",job_running:"Reading: {done} of {total} asked, {read} with a value.",job_done:"Read once: {read} of {total} with a value. Not kept up to date: follow a row to keep it.",job_stopped:"Stopped: {done} of {total} asked, {stopped} withdrawn.",job_reload:"The integration reloaded: the reads not yet asked were dropped.",read_once:"read once",follow:"Follow",follow_all:"Follow all",follow_none:"Follow none",follow_blocked:"disabled by its device",follow_pending:"{n} changes to apply: {enable} to follow, {disable} to stop following.",follow_reload:"Home Assistant reloads the integration about {s} s after an entity is enabled: the panel reloads with it, and reads under way stop.",follow_defaults_off:"{n} of them are followed by default (live values, states, counters): disabled, they are no longer read, their history stops, and dashboards or automations that use them no longer find them.",follow_apply:"Apply",follow_discard:"Discard",follow_done:"{enabled} enabled, {disabled} disabled.",follow_reload_soon:"Home Assistant reloads the integration in about {s} s.",follow_refused:"{n} not changed: disabled by their device or config entry, or not this integration's.",writes_pill_on:"Writes: on ({n}/{max})",writes_pill_off:"Writes: locked",open_switch:"Open writes switch",items_count:"{n} items",items_count_one:"1 item",fault_hide_zero:"Hide zero counters ({n})",fault_all_zero:"All read counters are at 0.",copy_all:"every day",copy_weekdays:"Monday \u2013 Friday",copy_weekend:"Saturday, Sunday",search_placeholder:"Search settings, sensors, codes, keys\u2026",search_clear:"Clear",filter_all:"All",filter_writable:"Writable",filter_followed:"Followed",filter_unread:"Unread",search_results:"{n} matching rows",search_results_one:"1 matching row",search_empty:"No row matches this search.",bar_remove_hint:"{range} \u2014 click to remove",clear_day:"Clear",follow_details:"Show details ({n})"},fr:{title:"Weishaupt",installation:"Installation",devices:"Appareils",definitions:"D\xE9finitions",programs:"Programmes hebdomadaires",loading:"Chargement\u2026",no_installation:"Aucune installation Weishaupt n'est charg\xE9e.",unavailable:"ebusd ne r\xE9pond pas : les valeurs affich\xE9es sont les derni\xE8res lues.",value:"Valeur",name:"Nom",age:"Lu",range:"Plage",write:"\xC9criture",entity:"Entit\xE9",open:"Ouvrir",comfort:"confort",regulation:"r\xE9gulation",read_only:"lecture seule",not_loaded:"non charg\xE9 par ebusd",not_listened:"non lu : aucune entit\xE9 activ\xE9e",waiting:"en attente de la premi\xE8re lecture",not_available:"non disponible",seconds_ago:"il y a {n} s",minutes_ago:"il y a {n} min",hours_ago:"il y a {n} h",days_ago:"il y a {n} j",passive:"envoy\xE9 par l'appareil",clock_offset:"Horloge ma\xEEtresse",clock_line:"{label} : {text}",clock_ahead:"{n} s d'avance",clock_behind:"{n} s de retard",clock_on_time:"\xE0 l'heure",software:"Logiciel",hardware:"Mat\xE9riel",address:"Adresse de bus",in_use:"Utilis\xE9es",source_bundled:"livr\xE9es avec l'int\xE9gration",source_file:"fichier \xE0 c\xF4t\xE9 de la configuration : {file}",refused:"Fichiers non utilis\xE9s",mismatches:"\xC9carts avec ebusd",named_from_metadata:"Entit\xE9s nomm\xE9es par les d\xE9finitions",not_named:"Entit\xE9s en attente d'un nom",messages:"Messages",usable:"{usable} sur {messages} charg\xE9s par ebusd comme d\xE9crits",writes:"\xC9critures",writes_off:"d\xE9sactiv\xE9es dans les options",switch_on:"interrupteur allum\xE9",switch_off:"interrupteur \xE9teint",capability:"checksum \xE0 l'ex\xE9cution : {value}",mode_follow:"suit l'ebusd en marche ({n} connus)",mode_pinned:"fix\xE9 ({n} connus)",per_hour:"{n} sur {max} cette heure",ebusd:"ebusd",unknown_addresses:"Adresses qui r\xE9pondent sans d\xE9finition",none:"aucun",day_unread:"pas encore lu",day_none:"aucune plage",editable:"modifiable par ses entit\xE9s de jour de programme",not_editable:"lecture seule : \xE9criture non prouv\xE9e sur cet appareil",not_read_program:"non charg\xE9 par ebusd",program_not_listened:"lu par aucune entit\xE9 activ\xE9e : lisez-le une fois maintenant, ou activez le capteur du programme pour le tenir \xE0 jour",write_hint:"Modifiez un r\xE9glage avec son bouton Modifier (l'interrupteur d'\xE9criture doit \xEAtre allum\xE9). Confort : \xE9crit aussit\xF4t et relu ; r\xE9gulation : apr\xE8s une confirmation dans ce panneau. Ouvrir affiche l'entit\xE9.",description:"Description",no_sensor:"pas de sonde",kept:"conserv\xE9e d'avant le rechargement, relue bient\xF4t",through:"par {circuit}",read_now:"Lire maintenant",read_cost:"{n} requ\xEAtes sur le bus, environ {s} s, une seule fois",read_queued:"{n} requ\xEAtes en file ; la grille se remplit au fil des r\xE9ponses",readable:"{usable} sur {readable} messages lisibles charg\xE9s par ebusd comme d\xE9crits",not_usable:"Messages non lus",reason_write_only:"\xE9criture seule",reason_device_absent:"appareil absent du bus",absent_circuit:"{circuit} : {n} messages, appareil absent du bus",reason_mismatch:"non charg\xE9 comme d\xE9crit",reason_other:"non lu",disabled:"d\xE9sactiv\xE9e",reloading:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : nouveau chargement\u2026",read_only_settings:"R\xE9glages laiss\xE9s en lecture seule",edit:"Modifier",write_now:"\xC9crire",cancel:"Annuler",confirm:"\xC9crire dans le r\xE9gulateur",confirm_clock:"Envoyer l'heure",confirm_title:"Confirmer : {setting} \u2014 {device}",current:"Valeur actuelle",new_value:"Nouvelle valeur",allowed:"Valeurs autoris\xE9es",path:"\xC9crit \xE0 l'adresse de bus {address}, registre {register}, depuis l'adresse source {source} ({source_text}). Relu juste apr\xE8s.",path_short:"adresse de bus {address}, registre {register}, depuis {source}",regulation_note:"Ce r\xE9glage modifie la r\xE9gulation du chauffage : il est \xE9crit apr\xE8s votre confirmation.",comfort_note:"R\xE9glage de confort : \xE9crit aussit\xF4t et relu.",writing:"\xC9criture\u2026",written_line:"{before} \u2192 {after}{frame} : {result}",not_written:"Non \xE9crit : {message}",not_offered_writes_disabled:"l'\xE9criture n'est pas activ\xE9e dans les options",not_offered:"non propos\xE9 sur cette installation : {reason}",switch_off_hint:"L'interrupteur d'\xE9criture est \xE9teint : allumez-le pour \xE9crire.",edit_days:"Modifier",write_days:"\xC9crire les jours modifi\xE9s",discard:"Abandonner les modifications",copy_to:"Copier vers",copy:"Copier",cost:"{days} jours modifi\xE9s : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",cost_one:"1 jour modifi\xE9 : jusqu'\xE0 {writes} \xE9critures (seuls les cr\xE9neaux chang\xE9s sont \xE9crits) ; {used} sur {max} cette heure",interrupted:"pas de r\xE9ponse de Home Assistant (connexion interrompue) : l'\xE9criture a pu partir ou non ; v\xE9rifiez la valeur relue",drag_hint:"Saisissez les plages, ou glissez sur la barre pour en ajouter une au quart d'heure ; un clic sur une plage la retire.",day_format:"\xE9crivez HH:MM-HH:MM, trois plages au plus, ou -",day_quarter:"les heures doivent \xEAtre des quarts d'heure, de 00:00 \xE0 24:00",day_order:"une plage doit finir apr\xE8s son d\xE9but",day_too_many:"trois plages au plus",day_overlap:"les plages ne doivent pas se chevaucher",set_clock:"Mettre \xE0 l'heure",clock_confirm:"Enverra l'heure de Home Assistant \xE0 la seconde 00 de la minute suivante ({send_at}), \xE0 l'adresse de bus fe depuis l'adresse source 31. Si le bus n'est pas libre dans les {late} s apr\xE8s la seconde 00, rien n'est envoy\xE9.",clock_sent:"Envoy\xE9 {requested} ({frame}) : {result}",clock_current:"Horloge ma\xEEtresse maintenant : {current}",col_device:"Appareil",col_menu:"Menu",col_label:"R\xE9glage",col_value:"Valeur",col_unit:"Unit\xE9",col_range:"Plage (pas) ou choix",col_writable:"Inscriptible",col_code:"Code constructeur",col_scheme:"Num\xE9rotation du code",code:"Code",code_title:"{scheme}, document {document}",sort_by_code:"Trier par code constructeur",report_codes:"Codes constructeur : {schemes}.",report:"Rapport imprimable",export_csv:"Exporter en CSV",report_title:"R\xE9glages de l'installation",report_subtitle:"{date} \xB7 d\xE9finitions {version} \xB7 lus par l'int\xE9gration Weishaupt de Home Assistant",report_no_factory:"Valeurs d'usine : les d\xE9finitions ne les donnent pas encore. Une valeur vide n'\xE9tait pas lue au moment du rapport.",report_blocked:"Le navigateur a bloqu\xE9 la fen\xEAtre du rapport : autorisez les fen\xEAtres pour Home Assistant et r\xE9essayez.",faults:"D\xE9fauts",fault_history:"M\xE9moire de d\xE9fauts",fault_counters:"Compteurs de d\xE9fauts",fault_log:"Journal de d\xE9fauts du manager syst\xE8me (entr\xE9e s\xE9lectionn\xE9e)",fault_code:"Code",fault_text:"Texte",fault_slot:"Emplacement",fault_values:"Valeurs enregistr\xE9es avec lui",fault_number:"D\xE9faut",fault_count:"Nombre",fault_none:"aucun d\xE9faut enregistr\xE9",fault_unordered:"Ordre inconnu : le pointeur de la derni\xE8re entr\xE9e n'est pas lu.",fault_no_time:"La chaudi\xE8re n'enregistre pas d'heure avec une entr\xE9e.",fault_log_fields:"Entr\xE9e {id} : code {code}, type {type}, origine {device}, {time}",fault_log_hint:"Le tableau de commande du manager syst\xE8me choisit l'entr\xE9e affich\xE9e ; en choisir une autre est une \xE9criture, que le panneau ne fait pas.",faults_unread:"{n} de ces messages ne sont lus par aucune entit\xE9 activ\xE9e.",faults_read_once:"Lus une fois \xE0 la demande : pas tenus \xE0 jour tant que leurs entit\xE9s ne sont pas activ\xE9es.",read_nothing:"Rien \xE0 demander : ces messages sont d\xE9j\xE0 lus par des entit\xE9s activ\xE9es ou en attente.",card_name:"Programme hebdomadaire Weishaupt",card_description:"La grille de la semaine d'un programme hebdomadaire d'un r\xE9gulateur Weishaupt.",card_no_entity:"Choisissez un capteur de programme de l'int\xE9gration Weishaupt dans les r\xE9glages de la carte.",card_missing:"{entity} n'existe pas ou est d\xE9sactiv\xE9 : activez-le dans Param\xE8tres \u2192 Entit\xE9s (les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s).",card_unavailable:"{entity} est indisponible : ebusd ou le r\xE9gulateur ne r\xE9pond pas.",card_unread:"pas encore lu",card_editor_entity:"Capteur de programme",card_editor_title:"Titre (facultatif)",card_editor_today:"Marquer aujourd'hui",card_editor_hint:"Les capteurs de programme sont cr\xE9\xE9s d\xE9sactiv\xE9s : un programme absent de la liste s'active dans Param\xE8tres \u2192 Entit\xE9s.",card_edit:"Modifier",card_edited_on:"Lu dans la m\xE9moire de {device} : modifiez ce programme l\xE0-bas.",edited_on_program:"Lu dans la m\xE9moire de {device} : modifiez {program} de {device} ; une modification envoy\xE9e ici serait acquitt\xE9e puis perdue.",edited_on_setting:"tenu par {device} : \xE0 modifier l\xE0-bas",stored_only_badge:"m\xE9moris\xE9 uniquement",stored_only_note:"M\xE9moris\xE9 dans cet appareil uniquement : non suivi par l'installation (l'ECS suit le manager de cascade).",card_type_hint:"Saisissez jusqu'\xE0 trois plages par jour, HH:MM-HH:MM, ou - pour aucune ; seuls les jours modifi\xE9s sont \xE9crits.",card_edit_admin:"Les jours sont modifi\xE9s par les administrateurs, ici ou dans le panneau Weishaupt.",card_not_writable:"Ce programme n'est pas prouv\xE9 inscriptible sur son appareil : lecture seule.",card_writing_day:"{day} : \xE9criture\u2026",card_written_day:"{day} : \xE9crit et relu",card_failed_day:"{day} : non \xE9crit : {message}",card_no_switch:"L'\xE9criture n'est pas activ\xE9e dans les options de l'int\xE9gration.",read_queued_one:"1 requ\xEAte en file (environ {s} s).",read_queued_n:"{n} requ\xEAtes en file (environ {s} s).",read_after_first_pass:"Elles passent apr\xE8s la premi\xE8re lecture qui suit un d\xE9marrage : {n} lectures encore dues, {wait}.",read_after_queue:"Elles passent apr\xE8s {n} lectures d\xE9j\xE0 dues, {wait}.",about_s:"environ {n} s",about_min:"environ {n} min",read_scope_menu:"Lire ce menu une fois",read_scope_device:"Lire cet appareil une fois",read_scope_all:"Tout lire une fois",read_scope_hint:"Les lignes qu'aucune entit\xE9 activ\xE9e ne suit sont lues une fois, au rythme du bus, apr\xE8s ce qu'attendent les entit\xE9s.",read_price_one:"1 requ\xEAte, {time}.",read_price_n:"{n} requ\xEAtes, {time}.",read_start:"D\xE9marrer",read_stop:"Arr\xEAter",dismiss:"Fermer",job_running:"Lecture : {done} sur {total} demand\xE9es, {read} avec une valeur.",job_done:"Lu une fois : {read} sur {total} avec une valeur. Pas tenu \xE0 jour : suivez une ligne pour la garder \xE0 jour.",job_stopped:"Arr\xEAt\xE9 : {done} sur {total} demand\xE9es, {stopped} retir\xE9es.",job_reload:"L'int\xE9gration a \xE9t\xE9 recharg\xE9e : les lectures pas encore demand\xE9es ont \xE9t\xE9 abandonn\xE9es.",read_once:"lu une fois",follow:"Suivre",follow_all:"Tout suivre",follow_none:"Ne rien suivre",follow_blocked:"d\xE9sactiv\xE9e par son appareil",follow_pending:"{n} changements \xE0 appliquer : {enable} \xE0 suivre, {disable} \xE0 ne plus suivre.",follow_reload:"Home Assistant recharge l'int\xE9gration environ {s} s apr\xE8s l'activation d'une entit\xE9 : le panneau se recharge avec elle, et les lectures en cours s'arr\xEAtent.",follow_defaults_off:"{n} d'entre elles sont suivies par d\xE9faut (valeurs instantan\xE9es, \xE9tats, compteurs) : d\xE9sactiv\xE9es, elles ne sont plus lues, leur historique s'arr\xEAte, et les tableaux de bord ou automatisations qui les utilisent ne les trouvent plus.",follow_apply:"Appliquer",follow_discard:"Annuler",follow_done:"{enabled} activ\xE9es, {disabled} d\xE9sactiv\xE9es.",follow_reload_soon:"Home Assistant recharge l'int\xE9gration dans environ {s} s.",follow_refused:"{n} non modifi\xE9es : d\xE9sactiv\xE9es par leur appareil ou leur entr\xE9e, ou pas de cette int\xE9gration.",writes_pill_on:"\xC9critures : actives ({n}/{max})",writes_pill_off:"\xC9critures : verrouill\xE9es",open_switch:"Ouvrir l'interrupteur",items_count:"{n} \xE9l\xE9ments",items_count_one:"1 \xE9l\xE9ment",fault_hide_zero:"Masquer les compteurs \xE0 0 ({n})",fault_all_zero:"Tous les compteurs lus sont \xE0 0.",copy_all:"tous les jours",copy_weekdays:"lundi \u2013 vendredi",copy_weekend:"samedi, dimanche",search_placeholder:"Rechercher un r\xE9glage, une sonde, un code, une cl\xE9\u2026",search_clear:"Effacer",filter_all:"Tout",filter_writable:"Modifiables",filter_followed:"Suivis",filter_unread:"Non lus",search_results:"{n} lignes correspondantes",search_results_one:"1 ligne correspondante",search_empty:"Aucune ligne ne correspond \xE0 cette recherche.",bar_remove_hint:"{range} \u2014 cliquer pour retirer",clear_day:"Vider",follow_details:"Voir le d\xE9tail ({n})"}},A={en:["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],fr:["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]};function q(o){let e=(o??"en").split("-")[0];return e in _e?e:"en"}function l(o,e,t={}){return(_e[o]?.[e]??_e.en[e]??e).replace(/\{(\w+)\}/g,(n,s)=>String(t[s]??`{${s}}`))}var De=3,fe=15;function C(o){let e=o.trim();if(e===""||e==="-")return{ranges:[]};let t=[];for(let r of e.split(",")){let n=/^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(r);if(!n)return{error:"day_format"};let[s,i,d,a]=n.slice(1).map(Number),c=s*60+i,_=d*60+a;if([i,a].some(p=>p%fe)||c>1440||_>1440||i>45||a>45)return{error:"day_quarter"};if(c>=_)return{error:"day_order"};t.push([c,_])}if(t.length>De)return{error:"day_too_many"};t.sort((r,n)=>r[0]-n[0]);for(let r=1;r<t.length;r++)if(t[r][0]<t[r-1][1])return{error:"day_overlap"};return{ranges:t}}function w(o){let e=Math.floor(o/60),t=o%60;return`${String(e).padStart(2,"0")}:${String(t).padStart(2,"0")}`}function I(o){return o.length?o.map(([e,t])=>`${w(e)}-${w(t)}`).join(", "):"-"}function Z(o,e){let t=s=>Math.round(Math.min(1,Math.max(0,s))*1440/fe)*fe,r=Math.min(t(o),t(e)),n=Math.max(t(o),t(e));return n===r&&(n=Math.min(1440,r+60)),[r,n]}function Oe(o,e,t){let[r,n]=Z(e,t),s=[];for(let[d,a]of o)d<=n&&a>=r?(r=Math.min(r,d),n=Math.max(n,a)):s.push([d,a]);let i=[...s,[r,n]].sort((d,a)=>d[0]-a[0]);return i.length>De?null:i}function qe(o){let[e,t]=o.split(":").map(r=>Number(r));return e*60+(t||0)}function Le(o){return o.map(([e,t])=>{let r=qe(e),n=qe(t);return{left:r/1440*100,width:Math.max(0,n-r)/1440*100,text:`${e}-${t}`}})}var F=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"];function Ne(o){let e={};return F.forEach((t,r)=>{let n=o[t],s=typeof n=="string"?C(n):null;e[String(r+1)]=s&&"ranges"in s?s.ranges.map(([i,d])=>[w(i),w(d)]):null}),e}function Ue(o,e){if(!o.startsWith("sensor."))return!1;let t=F.filter(n=>typeof e[n]=="string").length,r=Object.keys(e).filter(n=>!F.includes(n)&&!["friendly_name","icon","edited_on"].includes(n));return t>0&&r.length===0||t===0&&/program/.test(o)}function ze(o){return(o.getDay()+6)%7+1}function We(o,e){let t=o?.[e];if(!o||!t?.device_id||!t.translation_key)return null;let r={};for(let n of Object.values(o)){if(n.platform!=="weishaupt"||n.device_id!==t.device_id||!n.entity_id.startsWith("text."))continue;let s=F.findIndex(i=>n.translation_key===`${t.translation_key}_${i}`);s>=0&&(r[String(s+1)]=n.entity_id)}return Object.keys(r).length===F.length?r:null}function Fe(o,e){let t=Object.values(o??{}).find(s=>s.platform==="weishaupt"&&s.translation_key==="writes"),r=t?e[t.entity_id]:void 0;if(!t||!r)return null;let n=s=>typeof s=="number"?s:null;return{entity_id:t.entity_id,on:r.state==="on",used:n(r.attributes.writes_last_hour),max:n(r.attributes.max_writes_per_hour)}}var V=class extends b{constructor(){super(),this.language="en",this.unread="",this.today=0,this.now=-1,this.caption=""}render(){let e=this.language,t=A[e]??A.en,r=this.now>=0?this.now:(()=>{let s=new Date;return s.getHours()*60+s.getMinutes()})(),n=Math.min(100,Math.max(0,r/1440*100));return h`<table>
      ${this.caption?h`<caption class="visually-hidden">${this.caption}</caption>`:f}
      <thead>
        <tr>
          <th scope="col"><span class="visually-hidden">${l(e,"programs")}</span></th>
          <td class="scale" aria-hidden="true">
            ${[0,6,12,18,24].map(s=>h`<span style="left:${s/24*100}%">${s}</span>`)}
          </td>
        </tr>
      </thead>
      <tbody>
        ${t.map((s,i)=>{let d=this.days?.[String(i+1)],a=d==null?this.unread||l(e,"day_unread"):d.length?d.map(([c,_])=>`${c}-${_}`).join(", "):l(e,"day_none");return h`<tr class=${this.today===i+1?"today":""}>
            <th scope="row">${s}</th>
            <td>
              <div class="day" aria-hidden="true">
                ${(d??[]).length?Le(d).map(c=>h`<span class="bar" style="left:${c.left}%;width:${c.width}%"></span>`):f}
                ${this.today===i+1?h`<span class="now-line" style="left:${n}%"></span>`:f}
              </div>
              <div class="day-text">${a}</div>
            </td>
          </tr>`})}
      </tbody>
    </table>`}};V.properties={days:{attribute:!1},language:{type:String},unread:{type:String},today:{type:Number},now:{type:Number},caption:{type:String}},V.styles=H`
    :host {
      display: block;
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
    tbody th {
      font-weight: 400;
      width: 8em;
    }
    tr.today th {
      font-weight: 500;
      color: var(--primary-color);
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
    .scale span:first-child {
      transform: none;
    }
    .scale span:last-child {
      transform: translateX(-100%);
    }
    .day {
      position: relative;
      height: 14px;
      background-color: var(--secondary-background-color);
      background-image: linear-gradient(
        to right,
        transparent calc(25% - 0.5px),
        var(--divider-color) 25%,
        transparent calc(25% + 0.5px),
        transparent calc(50% - 0.5px),
        var(--divider-color) 50%,
        transparent calc(50% + 0.5px),
        transparent calc(75% - 0.5px),
        var(--divider-color) 75%,
        transparent calc(75% + 0.5px)
      );
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
    }
    .now-line {
      position: absolute;
      top: -2px;
      bottom: -2px;
      width: 2px;
      margin-left: -1px;
      background: var(--error-color);
      border-radius: 1px;
      pointer-events: none;
    }
    .day-text {
      font-size: 0.85em;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
  `;customElements.get("weishaupt-week-grid")||customElements.define("weishaupt-week-grid",V);var M="weishaupt-program-card",me="weishaupt-program-card-editor";function Ve(o){let e=t=>o.states[t].state==="unavailable"?1:0;return Object.keys(o.states).filter(t=>Ue(t,o.states[t].attributes)).sort((t,r)=>e(t)-e(r)||t.localeCompare(r))}var B=class extends b{constructor(){super(),this._results={},this._busy=!1,this._dragError={}}setConfig(e){if(!e||typeof e!="object")throw new Error("Invalid configuration");this._config={today:!0,...e}}getCardSize(){return 5}static getStubConfig(e){return{type:`custom:${M}`,entity:Ve(e)[0]??"",today:!0}}static getConfigElement(){return document.createElement(me)}render(){let e=q(this.hass?.language),t=this._config??{type:M},r=t.entity,n=r?this.hass?.states[r]:void 0,s=t.title||n?.attributes.friendly_name||l(e,"card_name"),i;if(!r)i=h`<p class="message">${l(e,"card_no_entity")}</p>`;else if(!n)i=h`<p class="message">${l(e,"card_missing",{entity:r})}</p>`;else if(n.state==="unavailable")i=h`<p class="message">${l(e,"card_unavailable",{entity:r})}</p>`;else{let d=Ne(n.attributes),a=this.hass.user?.is_admin?We(this.hass.entities,r):null;i=this._draft&&a?this._editor(d,a,e):h`<weishaupt-week-grid
              .days=${d}
              language=${e}
              unread=${l(e,"card_unread")}
              caption=${s}
              today=${t.today===!1?0:ze(new Date)}
            ></weishaupt-week-grid>
            ${typeof n.attributes.edited_on=="string"?h`<p class="secondary">${l(e,"card_edited_on",{device:n.attributes.edited_on})}</p>`:null}
            ${a?h`<div class="actions">
                  <button class="link" @click=${()=>this._start(d)}>${l(e,"card_edit")}</button>
                </div>`:null}
            ${this._resultLines()}`}return h`<div class="card"><h2>${s}</h2>${i}</div>`}_current(e,t){let r=e[t];return r?I(r.map(([n,s])=>[Ie(n),Ie(s)])):null}_start(e){let t={};for(let r=1;r<=7;r++)t[String(r)]=this._current(e,String(r))??"";this._draft=t,this._results={},this._dragError={}}_setDay(e,t){if(this._draft={...this._draft,[e]:t},this._dragError[e]){let r={...this._dragError};delete r[e],this._dragError=r}}_changed(e){let t=this._draft??{};return Object.keys(t).filter(r=>{let n=this._current(e,r);if(n===null&&t[r].trim()==="")return!1;let s=C(t[r]);return("ranges"in s?I(s.ranges):t[r])!==n})}_copy(e,t){let r=this._draft[e],n=t==="all"?["1","2","3","4","5","6","7"]:t==="weekdays"?["1","2","3","4","5"]:t==="weekend"?["6","7"]:[t],s={...this._draft};for(let i of n)i!==e&&(s[i]=r);this._draft=s}_dragStart(e,t){let r=e.currentTarget;if(e.target.classList.contains("bar"))return;let n=r.getBoundingClientRect(),s=(e.clientX-n.left)/n.width;this._drag={day:t,from:s,element:r};let[i,d]=Z(s,s);this._dragPreview={day:t,start:i,end:d},r.setPointerCapture(e.pointerId)}_dragMove(e){let t=this._drag;if(!t)return;let r=t.element.getBoundingClientRect(),[n,s]=Z(t.from,(e.clientX-r.left)/r.width);this._dragPreview={day:t.day,start:n,end:s}}_dragCancel(){this._drag=void 0,this._dragPreview=void 0}_dragEnd(e){let t=this._drag;if(this._drag=void 0,this._dragPreview=void 0,!t)return;let r=t.element.getBoundingClientRect(),n=C(this._draft[t.day]);if(!("ranges"in n))return;let s=Oe(n.ranges,t.from,(e.clientX-r.left)/r.width);s?this._setDay(t.day,I(s)):this._dragError={...this._dragError,[t.day]:"day_too_many"}}_removeRange(e,t){let r=C(this._draft[e]);"ranges"in r&&this._setDay(e,I(r.ranges.filter((n,s)=>s!==t)))}async _write(e,t){let r=q(this.hass.language),n=A[r]??A.en;this._busy=!0;let s={};for(let i of this._changed(e)){let d=n[Number(i)-1];this._results={...s,[i]:{text:l(r,"card_writing_day",{day:d}),error:!1}};try{await this.hass.callService("text","set_value",{value:this._draft[i]},{entity_id:t[i]}),s[i]={text:l(r,"card_written_day",{day:d}),error:!1}}catch(a){s[i]={text:l(r,"card_failed_day",{day:d,message:a.message??""}),error:!0}}}this._results=s,this._busy=!1,Object.values(s).some(i=>i.error)||(this._draft=void 0)}_resultLines(){let e=Object.values(this._results),t=q(this.hass?.language);return e.length?h`<div class="results" role="status">
          ${e.map(r=>h`<div class=${r.error?"error":"secondary"}>${r.text}</div>`)}
          ${this._busy?f:h`<button class="ghost" type="button" @click=${()=>this._results={}}>${l(t,"dismiss")}</button>`}
        </div>`:null}_editor(e,t,r){let n=A[r]??A.en,s=this._draft,i=this._changed(e),d=Object.fromEntries(Object.entries(s).map(([_,p])=>{let u=C(p);return[_,"error"in u?u.error:null]})),a=Object.values(d).some(Boolean),c=Fe(this.hass.entities,this.hass.states);return h`<p class="secondary">${l(r,"drag_hint")}</p>
      <div class="scale" aria-hidden="true">
        ${[0,6,12,18,24].map(_=>h`<span style="left:${_/24*100}%">${_}</span>`)}
      </div>
      ${n.map((_,p)=>{let u=String(p+1),g=C(s[u]),T="ranges"in g?g.ranges:[],ee=d[u]??this._dragError[u]??null,$=this._dragPreview?.day===u?this._dragPreview:void 0;return h`<div class=${i.includes(u)?"day changed":"day"}>
          <label for="d${u}">${_}</label>
          <div
            class="bar-track"
            aria-hidden="true"
            @pointerdown=${m=>this._dragStart(m,u)}
            @pointermove=${m=>this._dragMove(m)}
            @pointerup=${m=>this._dragEnd(m)}
            @pointercancel=${()=>this._dragCancel()}
          >
            ${T.map(([m,y],Be)=>h`<span
                class="bar"
                title=${l(r,"bar_remove_hint",{range:`${w(m)}-${w(y)}`})}
                style="left:${m/1440*100}%;width:${(y-m)/1440*100}%"
                @click=${()=>this._removeRange(u,Be)}
              ></span>`)}
            ${$?h`<span
                    class="bar preview"
                    style="left:${$.start/1440*100}%;width:${($.end-$.start)/1440*100}%"
                  ></span>
                  <span
                    class="drag-label"
                    style="left:${($.start+$.end)/2880*100}%"
                  >${w($.start)}–${w($.end)}</span>`:f}
          </div>
          <div class="day-controls">
            <input id="d${u}" type="text" .value=${s[u]} aria-invalid=${ee?"true":"false"}
              placeholder=${e[u]==null?l(r,"card_unread"):""}
              @input=${m=>this._setDay(u,m.target.value)} />
            <button
              class="ghost"
              type="button"
              ?disabled=${s[u].trim()===""||s[u].trim()==="-"}
              @click=${()=>this._setDay(u,"-")}
            >
              ${l(r,"clear_day")}
            </button>
            <select aria-label=${l(r,"copy_to")} @change=${m=>{let y=m.target;y.value&&this._copy(u,y.value),y.value=""}}>
              <option value="">${l(r,"copy_to")}…</option>
              <option value="all">${l(r,"copy_all")}</option>
              <option value="weekdays">${l(r,"copy_weekdays")}</option>
              <option value="weekend">${l(r,"copy_weekend")}</option>
              ${n.map((m,y)=>y===p?f:h`<option value=${String(y+1)}>${m}</option>`)}
            </select>
          </div>
          ${ee?h`<div class="error" role="alert">${l(r,ee)}</div>`:null}
          ${this._results[u]?h`<div class=${this._results[u].error?"error":"secondary"}>${this._results[u].text}</div>`:null}
        </div>`})}
      ${c?h`<p class="secondary">
              ${l(r,i.length===1?"cost_one":"cost",{days:i.length,writes:i.length*3,used:c.used??"?",max:c.max??"?"})}
            </p>
            ${c.on?null:h`<p class="error">
                  ${l(r,"switch_off_hint")}
                  <button
                    class="link"
                    type="button"
                    @click=${()=>this.dispatchEvent(new CustomEvent("hass-more-info",{detail:{entityId:c.entity_id},bubbles:!0,composed:!0}))}
                  >
                    ${l(r,"open_switch")}
                  </button>
                </p>`}`:h`<p class="error">${l(r,"card_no_switch")}</p>`}
      <div class="actions">
        <button class="link" ?disabled=${this._busy} @click=${()=>{this._draft=void 0,this._results={}}}>
          ${l(r,"discard")}
        </button>
        <button class="primary" ?disabled=${this._busy||a||!i.length||!c?.on}
          @click=${()=>this._write(e,t)}>${l(r,"write_days")}</button>
      </div>`}};B.properties={hass:{attribute:!1},_config:{state:!0},_draft:{state:!0},_results:{state:!0},_busy:{state:!0},_dragPreview:{state:!0},_dragError:{state:!0}},B.styles=H`
    .card {
      background: var(--ha-card-background, var(--card-background-color));
      color: var(--primary-text-color);
      border-radius: var(--ha-card-border-radius, 12px);
      border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
      box-shadow: var(--ha-card-box-shadow, none);
      padding: 12px 16px 16px;
    }
    h2 {
      font-size: var(--ha-card-header-font-size, 20px);
      font-weight: 400;
      margin: 0 0 8px;
    }
    .message,
    .secondary {
      color: var(--secondary-text-color);
      margin: 0;
    }
    .secondary {
      font-size: 0.9em;
    }
    .error {
      color: var(--error-color);
      font-size: 0.9em;
    }
    .scale {
      position: relative;
      height: 1.4em;
      margin: 6px 0 2px 7em;
    }
    .scale span {
      position: absolute;
      transform: translateX(-50%);
      color: var(--secondary-text-color);
      font-size: 0.8em;
    }
    .scale span:first-child {
      transform: none;
    }
    .scale span:last-child {
      transform: translateX(-100%);
    }
    .day {
      display: grid;
      grid-template-columns: 6.5em minmax(0, 1fr);
      gap: 4px 8px;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid var(--divider-color);
    }
    .day .day-controls,
    .day .error,
    .day .secondary {
      grid-column: 2 / -1;
    }
    .day-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 6px;
      align-items: center;
    }
    .day-controls input {
      flex: 1 1 10em;
    }
    .bar-track {
      position: relative;
      height: 20px;
      cursor: crosshair;
      touch-action: none;
      background-color: var(--secondary-background-color);
      background-image: linear-gradient(
        to right,
        transparent calc(25% - 0.5px),
        var(--divider-color) 25%,
        transparent calc(25% + 0.5px),
        transparent calc(50% - 0.5px),
        var(--divider-color) 50%,
        transparent calc(50% + 0.5px),
        transparent calc(75% - 0.5px),
        var(--divider-color) 75%,
        transparent calc(75% + 0.5px)
      );
      border-radius: 4px;
    }
    .bar {
      position: absolute;
      top: 0;
      bottom: 0;
      background: var(--primary-color);
      border-radius: 4px;
      cursor: pointer;
    }
    .bar:hover {
      background: var(--error-color);
    }
    .bar.preview {
      opacity: 0.45;
      pointer-events: none;
    }
    .drag-label {
      position: absolute;
      top: -22px;
      transform: translateX(-50%);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.78em;
      white-space: nowrap;
      background: var(--primary-text-color);
      color: var(--card-background-color);
      pointer-events: none;
      z-index: 3;
    }
    button.ghost {
      border: 0;
      background: none;
      border-radius: 6px;
      padding: 2px 6px;
      color: var(--secondary-text-color);
    }
    button.ghost:hover:not(:disabled) {
      background: var(--secondary-background-color);
      color: var(--primary-text-color);
    }
    .day.changed label {
      color: var(--primary-color);
      font-weight: 500;
    }
    input,
    select {
      font: inherit;
      padding: 4px 6px;
      min-width: 0;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
    input[aria-invalid="true"] {
      border-color: var(--error-color);
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      margin-top: 8px;
    }
    .results {
      margin-top: 8px;
    }
    button {
      font: inherit;
      cursor: pointer;
    }
    button.link {
      border: 1px solid var(--divider-color);
      background: none;
      border-radius: 6px;
      padding: 2px 10px;
      color: var(--primary-color);
    }
    button.primary {
      border: 0;
      border-radius: 6px;
      padding: 4px 12px;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
  `;function Ie(o){let[e,t]=o.split(":").map(Number);return e*60+(t||0)}var K=class extends b{setConfig(e){this._config=e}_change(e){this._config={...this._config,...e},this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:this._config},bubbles:!0,composed:!0}))}render(){let e=q(this.hass?.language),t=this.hass?Ve(this.hass):[],r=this._config??{type:`custom:${M}`};return h`<div class="editor">
      <label
        >${l(e,"card_editor_entity")}
        <select @change=${n=>this._change({entity:n.target.value})}>
          <option value="" ?selected=${!r.entity}>…</option>
          ${t.map(n=>h`<option value=${n} ?selected=${n===r.entity}>
            ${this.hass.states[n].attributes.friendly_name??n}
          </option>`)}
        </select>
      </label>
      <p class="hint">${l(e,"card_editor_hint")}</p>
      <label
        >${l(e,"card_editor_title")}
        <input type="text" .value=${r.title??""}
          @input=${n=>this._change({title:n.target.value||void 0})} />
      </label>
      <label class="check"
        ><input type="checkbox" .checked=${r.today!==!1}
          @change=${n=>this._change({today:n.target.checked})} />
        ${l(e,"card_editor_today")}</label
      >
    </div>`}};K.properties={hass:{attribute:!1},_config:{state:!0}},K.styles=H`
    .editor {
      display: grid;
      gap: 12px;
    }
    label {
      display: grid;
      gap: 4px;
      color: var(--secondary-text-color);
    }
    .hint {
      margin: -6px 0 0;
      font-size: 0.85em;
      color: var(--secondary-text-color);
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    select,
    input[type="text"] {
      font: inherit;
      padding: 6px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 6px;
    }
  `;customElements.get(M)||customElements.define(M,B);customElements.get(me)||customElements.define(me,K);var G=window;G.customCards=G.customCards??[];if(!G.customCards.some(o=>o.type===M)){let o=q(navigator.language);G.customCards.push({type:M,name:l(o,"card_name"),description:l(o,"card_description")})}export{B as WeishauptProgramCard,K as WeishauptProgramCardEditor};
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
